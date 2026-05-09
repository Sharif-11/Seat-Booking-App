import { io, Socket } from 'socket.io-client'
let socket: Socket | null = null

export const getSocket = (): Socket => {
  console.log('🔌 getSocket called') // add this
  if (!socket) {
    socket = io('http://138.252.124.38:8000', {
      path: '/ws/socket.io',
      transports: ['websocket'],
    })
  }
  return socket
}
