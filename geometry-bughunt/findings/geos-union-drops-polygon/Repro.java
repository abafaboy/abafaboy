// Same two triangles through JTS (public API only).
// Build/run: javac -cp jts-core.jar Repro.java && java -cp jts-core.jar:. Repro
import org.locationtech.jts.JTSVersion;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.io.WKTReader;
import org.locationtech.jts.operation.overlayng.OverlayNG;
import org.locationtech.jts.operation.overlayng.OverlayNGRobust;

public class Repro {
  public static void main(String[] args) throws Exception {
    WKTReader r = new WKTReader();
    Geometry a = r.read("POLYGON ((1 1, -1e-20 0, 1 0, 1 1))");
    Geometry b = r.read("POLYGON ((0 0, 1 1, 0 1, 0 0))");
    System.out.println("JTS " + JTSVersion.CURRENT_VERSION);
    System.out.println("isValid(A)=" + a.isValid() + " isValid(B)=" + b.isValid()
        + " area(A)=" + a.getArea() + " area(B)=" + b.getArea());
    String[] names = {"union", "intersection", "B - A", "A - B", "symdifference"};
    Geometry[][] args2 = {{a, b}, {a, b}, {b, a}, {a, b}, {a, b}};
    int[] ops = {OverlayNG.UNION, OverlayNG.INTERSECTION, OverlayNG.DIFFERENCE,
                 OverlayNG.DIFFERENCE, OverlayNG.SYMDIFFERENCE};
    String[] expected = {"~1.0", "~5e-21", "~0.5", "~0.5", "~1.0"};
    for (int i = 0; i < ops.length; i++) {
      Geometry g = OverlayNGRobust.overlay(args2[i][0], args2[i][1], ops[i]);
      System.out.printf("OverlayNGRobust %-13s area = %-22s (expected %s)  %s%n",
          names[i], g.getArea(), expected[i], g);
    }
  }
}
