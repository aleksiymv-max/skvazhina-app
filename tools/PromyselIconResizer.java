import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import javax.imageio.ImageIO;

/**
 * Offline, dependency-free Promysel icon renderer for GitHub Actions.
 * Standard JDK ImageIO converts the JPEG embedded in the project SVG to PNG.
 * Invocation: java PromyselIconResizer.java source.jpg 1024 app.png 192 icon.png
 */
public final class PromyselIconResizer {
    public static void main(String[] args) throws Exception {
        if (args.length < 3 || args.length % 2 != 1) {
            throw new IllegalArgumentException("Usage: source.jpg size output.png [size output.png...]");
        }
        BufferedImage source = ImageIO.read(new File(args[0]));
        if (source == null) throw new IllegalStateException("Cannot read embedded JPEG");
        if (source.getWidth() != source.getHeight()) {
            throw new IllegalStateException("Expected square Promysel icon");
        }
        for (int i = 1; i < args.length; i += 2) {
            int size = Integer.parseInt(args[i]);
            if (size < 16 || size > 2048) throw new IllegalArgumentException("Invalid image size");
            File output = new File(args[i + 1]);
            File parent = output.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs()) {
                throw new IllegalStateException("Unable to create " + parent);
            }
            BufferedImage icon = new BufferedImage(size, size, BufferedImage.TYPE_INT_RGB);
            Graphics2D graphics = icon.createGraphics();
            try {
                graphics.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
                graphics.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
                graphics.drawImage(source, 0, 0, size, size, null);
            } finally {
                graphics.dispose();
            }
            if (!ImageIO.write(icon, "png", output)) {
                throw new IllegalStateException("PNG encoder missing: " + output);
            }
            System.out.println("Rendered " + output + " (" + size + "x" + size + ")");
        }
    }
}
