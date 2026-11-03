package ru.promysel.promysel

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Launcher icon dots on Android follow active notifications, so maintain a
 * single low-priority notification with the unread task count.
 * This does not pretend to be background push delivery.
 */
class MainActivity : FlutterActivity() {
    private val channel = "ru.promysel/task_launcher_badge"
    private val badgeChannel = "promysel_task_unread"
    private val badgeId = 19148
    private val requestId = 19149
    private var unreadCount: Int = 0

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channel).setMethodCallHandler { call, result ->
            when (call.method) {
                "setCount" -> {
                    unreadCount = (call.argument<Int>("count") ?: 0).coerceAtLeast(0)
                    showBadge()
                    result.success(null)
                }
                "requestPermission" -> {
                    if (Build.VERSION.SDK_INT >= 33 &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                    ) {
                        requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), requestId)
                    } else {
                        showBadge()
                    }
                    result.success(null)
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == requestId &&
            grantResults.isNotEmpty() &&
            grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            showBadge()
        }
    }

    private fun showBadge() {
        if (Build.VERSION.SDK_INT < 26) return
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (unreadCount == 0) {
            manager.cancel(badgeId)
            return
        }
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return
        }

        val notificationChannel = NotificationChannel(
            badgeChannel, "Задания Промысел", NotificationManager.IMPORTANCE_LOW
        )
        notificationChannel.setShowBadge(true)
        notificationChannel.setSound(null, null)
        manager.createNotificationChannel(notificationChannel)

        val intent = packageManager.getLaunchIntentForPackage(packageName)
        val pending = if (intent == null) null else PendingIntent.getActivity(
            this, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = Notification.Builder(this, badgeChannel)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Промысел — новые задания")
            .setContentText("Непрочитанных уведомлений: $unreadCount")
            .setNumber(unreadCount)
            .setBadgeIconType(Notification.BADGE_ICON_SMALL)
            .setOnlyAlertOnce(true)
            .setAutoCancel(false)
        if (pending != null) notification.setContentIntent(pending)
        manager.notify(badgeId, notification.build())
    }
}
