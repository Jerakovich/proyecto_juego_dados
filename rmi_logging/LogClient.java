import java.rmi.Naming;

public class LogClient {
    public static void main(String[] args) {
        try {
            if (args.length < 4) {
                System.out.println("Uso: java LogClient timestamp tipo juego_id operacion [equipo] [jugador] [valor]");
                return;
            }

            StringBuilder log = new StringBuilder();
            for (String arg : args) {
                log.append(arg).append(",");
            }
            // Eliminar la última coma
            log.setLength(log.length() - 1);

            LogService service = (LogService) Naming.lookup("rmi://localhost/LogService");
            service.registrarLog(log.toString());

        } catch (Exception e) {
            System.err.println("Error en LogClient: " + e.getMessage());
        }
    }
}
