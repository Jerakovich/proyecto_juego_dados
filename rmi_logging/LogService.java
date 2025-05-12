import java.rmi.Remote;
import java.rmi.RemoteException;

public interface LogService extends Remote {
    void registrarLog(String log) throws RemoteException;
}
