#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdlib.h>
#include <stdio.h>

#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")

int main(int argc, char* argv[])
{
    WSADATA wsaData;
    SOCKET sock_id = INVALID_SOCKET;

    int iResult = WSAStartup(MAKEWORD(2,2), &wsaData);
    if(iResult != 0)
    {
        perror("WSAStartup");
        return -1;
    }

    sock_id = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if(sock_id == INVALID_SOCKET)
    {
        perror("socket()");
        WSACleanup();
        return -1;
    }

    if(argc == 3)
    {
        struct addrinfo *result = NULL, hints;
        ZeroMemory(&hints, sizeof(hints));
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        hints.ai_protocol = IPPROTO_TCP;
        iResult = getaddrinfo(argv[1], argv[2], &hints, &result);
        if(iResult != 0)
        {
            struct sockaddr_in sockAddr;
            sockAddr.sin_family = AF_INET;
            sockAddr.sin_addr.S_un.S_addr = inet_addr(argv[2]);
            sockAddr.sin_port = htons(atoi(argv[2]));
            iResult = connect(sock_id, (SOCKADDR*) &sockAddr, (int)sizeof(sockAddr));
        }
        else
        {
            iResult = connect(sock_id, result->ai_addr, (int)result->ai_addrlen);
        }

        freeaddrinfo(result);
        if(iResult == SOCKET_ERROR)
        {
            closesocket(sock_id);
            sock_id = INVALID_SOCKET;
        }
        
    }

    shutdown(sock_id, SD_SEND);
    closesocket(sock_id);
    WSACleanup();

    return 0;
}
