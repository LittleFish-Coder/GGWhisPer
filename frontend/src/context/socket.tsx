import React, { createContext, useContext, useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";

interface SocketContextType {
    socket: Socket | null;
    isConnected: boolean;
}

const SOCKET_URL = "35.192.107.93:8888";
const SOCKET_OPTIONS = {
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: 5,
    timeout: 60000,
    autoConnect: true,
};

const SocketContext = createContext<SocketContextType>({
    socket: null,
    isConnected: false,
});

export const useSocket = () => {
    const context = useContext(SocketContext);
    if (!context) {
        throw new Error("useSocket must be used within a SocketProvider");
    }
    return context;
};

export const SocketProvider: React.FC<{ children: React.ReactNode }> = ({
    children,
}) => {
    const [socket, setSocket] = useState<Socket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const socketInstance = io(SOCKET_URL, SOCKET_OPTIONS);

        socketInstance.on("connect", () => {
            console.log("Socket connected successfully");
            setIsConnected(true);
        });

        socketInstance.on("disconnect", (reason) => {
            console.log("Socket disconnected:", reason);
            setIsConnected(false);
        });

        socketInstance.on("connect_error", (error) => {
            console.error("Socket connection error:", error);
            setIsConnected(false);
        });

        socketInstance.on("reconnect", (attemptNumber) => {
            console.log(`Reconnected after ${attemptNumber} attempts`);
            setIsConnected(true);
        });

        setSocket(socketInstance);

        return () => {
            if (socketInstance.connected) {
                socketInstance.disconnect();
            }
        };
    }, []);

    return (
        <SocketContext.Provider value={{ socket, isConnected }}>
            {children}
        </SocketContext.Provider>
    );
};
