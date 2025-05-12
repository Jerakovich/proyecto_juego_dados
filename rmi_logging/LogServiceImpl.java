import java.rmi.server.UnicastRemoteObject;
import java.rmi.RemoteException;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;

public class LogServiceImpl extends UnicastRemoteObject implements LogService {

    protected LogServiceImpl() throws RemoteException {
        super();
    }

    @Override
    public void registrarLog(String log) throws RemoteException {
        String timestamp = LocalDateTime.now().toString();
        String linea = timestamp + ", " + log + "\n";
        System.out.print("Registro recibido: " + linea);

        try (FileWriter writer = new FileWriter("logs_centralizados.txt", true)) {
            writer.write(linea);
        } catch (IOException e) {
            System.err.println("Error escribiendo en log: " + e.getMessage());
        }
    }
}
