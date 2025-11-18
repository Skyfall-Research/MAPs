import express from "express";
import http from "http";
import { Server } from "socket.io";
import cors from "cors";
import { createV1Router } from "./routes/index.js";

const app = express();
const server = http.createServer(app);


// CORS configuration - use environment variable for origin, fallback to localhost
// Support multiple origins separated by comma
const corsOriginEnv = process.env.CORS_ORIGIN || "http://localhost:3001";
const corsOrigin = corsOriginEnv.includes(',')
    ? corsOriginEnv.split(',').map(o => o.trim())
    : corsOriginEnv;

const io = new Server(server, {
    pingTimeout: 60 * 15 * 1000,
    cors: {
        origin: corsOrigin,
        methods: ["GET", "POST"],
        credentials: true
    }
});
const parks = {};

app.use(cors({
    origin: Array.isArray(corsOrigin) ? corsOrigin : [corsOrigin],
    credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.static("public"));

// Only mount visualization router if --vis flag is passed
if (process.argv.includes('--vis')) {
    app.use("/v1", createV1Router({ parks, io, visUpdateFn: updateParkState }));
} else {
    app.use("/v1", createV1Router({ parks, io }));
}

io.on("connection", (socket) => {
    console.log("Client connected");
    
    // for (let i = 0; i < parks.length; i++) {
    //     updateParkState({ io, park: parks[i], parkId: i });
    // }
    
    socket.on("create", () => {
    });
    
    socket.on("proceed", () => {
        for (let i = 0; i < parks.length; i++) {
            updateParkState({ io, park: parks[i], parkId: i });
        }
    });
});


function updateParkState({ io, park, parkId=-1, state_type="full_state", midday_state=null, full_state=null, tick=-1 }) {
    if (io.sockets.sockets.size == 0) {
        return;
    }

    let data = {};

    if (state_type == "mid_day") {
        let state = midday_state !== null ? midday_state : park.calculateMiddayState();
        state['state'] = {parkId: parkId};
        state['tick'] = tick;
        data = state;
    } else if (state_type == "exit_time") {
        data = {
            guests: park.guests.filter(guest => !guest.exited).map(guest => guest.midday_format()),
        };
        data['tick'] = tick;
        data['state'] = {parkId: parkId};
    } else { // full_state or day_end
        let state = full_state !== null ? full_state : park.calculateFullState()
        state['state']['parkId'] = parkId
        state['tick'] = tick;
        data = state;
    }

    io.emit("game_update", {
        state_type: state_type,
        data: data
    });
}

const park_port = process.env.MAP_PORT || 3000;
server.listen(park_port, () =>
    console.log(`Server running on port ${park_port} (http://localhost:${park_port})`)
);

process.on( 'SIGINT', function() {
  // console.log( "\nGracefully shutting down from SIGINT" );
  process.exit( );
})

process.on( 'SIGTERM', function() {
  // console.log( "\nGracefully shutting down from SIGTERM" );
  process.exit( );
})

process.on( 'SIGHUP', function() {
  // console.log( "\nGracefully shutting down from SIGHUP" );
  process.exit( );
})

process.on( 'SIGQUIT', function() {
  // console.log( "\nGracefully shutting down from SIGQUIT" );
  process.exit( );
})
