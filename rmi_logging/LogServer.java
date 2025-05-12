import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class LogServer {
    public static void main(String[] args) {
        try {
            // Obtener host y puerto desde variables de entorno
            String host = System.getenv("RMI_HOST");
            String portStr = System.getenv("RMI_PORT");

            if (host == null) host = "localhost";
            if (portStr == null) portStr = "1099";

            int port = Integer.parseInt(portStr);

            // Iniciar registro RMI
            LocateRegistry.createRegistry(port);

            // Crear e iniciar servicio
            LogService service = new LogServiceImpl();
            String url = "rmi://" + host + ":" + port + "/LogService";
            Naming.rebind(url, service);

            System.out.println("🟢 Servidor RMI de Logs iniciado en " + url);
        } catch (Exception e) {
            System.err.println("❌ Error en LogServer: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
