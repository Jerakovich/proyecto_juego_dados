import java.rmi.Naming;
import java.rmi.registry.LocateRegistry;

public class LogServer {
    public static void main(String[] args) {
        try {
            LocateRegistry.createRegistry(1099);
            LogService service = new LogServiceImpl();
            Naming.rebind("rmi://localhost/LogService", service);
            System.out.println("🟢 Servidor RMI de Logs iniciado...");
        } catch (Exception e) {
            System.err.println("Error en LogServer: " + e.getMessage());
        }
    }
}
