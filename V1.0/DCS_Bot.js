const { Client, GatewayIntentBits } = require('discord.js');
const { joinVoiceChannel, VoiceConnectionStatus } = require('@discordjs/voice');
const prism = require('prism-media');
const path = require('path'); 
const fs = require('fs');
const ini = require('ini');

const configPath = path.join(__dirname, 'config.ini');
const configFile = fs.readFileSync(configPath, 'utf-8');
const config = ini.parse(configFile);

const DISCORD_TOKEN = config.DISCORD.BOT_TOKEN;
const dsp = require('./dsp_processor.js');

// 🚀 引入外部解耦的標準 REST/Local LLM 心智模組
const llm = require('./llm_client.js');

const client = new Client({
    intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent]
});

let audioChunks = [];
let opusStream = null;
let pcmDecoder = null;

// 🔒 100% 航空級匿名去識別化正名：targetPilotId！拒絕任何隱私特徵殘留！
function setupVoiceReceiver(connection, targetPilotId) {
    console.log(`[Gateway V3.7] 真空解耦調度中樞就位。唯一守聽飛行員 ID: ${targetPilotId}`);

    connection.receiver.speaking.on('start', function(userId) {
        if (userId !== targetPilotId) return;
        console.log("\n🟢 === [PTT ON] 飛行員開始發言 ===");
        audioChunks = []; 
        opusStream = connection.receiver.subscribe(userId, { mode: 'opus' });
        pcmDecoder = new prism.opus.Decoder({ rate: 48000, channels: 2, frameSize: 960 });
        opusStream.pipe(pcmDecoder);
        pcmDecoder.on('data', chunk => audioChunks.push(chunk));
    });

    connection.receiver.speaking.on('end', function(userId) {
        if (userId !== targetPilotId) return;
        if (!opusStream) return;

        console.log("🔴 === [PTT OFF] 飛行員閉嘴。發動純記憶體 DSP 識別... ===");
        
        // ⏱️ 實體層 Facts 時間雷達 A：開啟全鏈路計時鋼印
        console.time("[📋 實體層 Facts] 本地全閉環分布式總時延");

        opusStream.destroy();
        if (pcmDecoder) pcmDecoder.destroy();
        opusStream = null;
        pcmDecoder = null;

        const finalMemoryWav = dsp.processAudioInMemory(audioChunks);

        if (finalMemoryWav) {
            // 軌道一：向本地 Python 獲取水晶文字
            fetch('http://localhost:5002/whisper', {
                method: 'POST',
                headers: { 'Content-Type': 'audio/wav', 'Content-Length': finalMemoryWav.length },
                body: finalMemoryWav
            })
            .then(res => res.json())
            .then(data => {
                const recognizedText = data.text;
                if (!recognizedText || recognizedText.toLowerCase() === 'you') return;
                
                console.log(`\n[🚀 聽覺大閘出字成功]: '${recognizedText}'`);

                // 🚀 軌道二：同步串行拋射，0% 贅肉！
                return llm.sendPromptToCloud(recognizedText)
                .then(llmReply => {
                    console.log("\n====================================");
                    console.log("[🧠 航空級去識別化大閉環通車大成功!]:");
                    console.log(`[🚀 聽到 飛行員 指令]: '${recognizedText}'`);
                    console.log(`[🎙️ 副駕駛戰術台詞]: '${llmReply}'`);
                    
                    // ⏱️ 實體層 Facts 時間雷達 B：原地結算並列印真實總時延毫秒數！
                    console.timeEnd("[📋 實體層 Facts] 本地全閉環分布式總時延");
                    console.log("====================================\n");
                });
            })
            .catch(err => console.log("[Error] 雙軌分布式心智鏈路異常: " + err.message));
        }
    });
}

client.on('messageCreate', function(message) {
    if (message.content === '!join') {
        const voiceChannel = message.member.voice.channel;
        if (!voiceChannel) return;
        
        const connection = joinVoiceChannel({
            channelId: voiceChannel.id,
            guildId: message.guild.id,
            adapterCreator: message.guild.voiceAdapterCreator,
            selfDeaf: false,
            selfMute: true
        });
        
        // 🔒 自動獲取發送指令的實體飛行員 ID 傳入，動態咬合，0% 靜態暴露！
        connection.on(VoiceConnectionStatus.Ready, () => setupVoiceReceiver(connection, message.author.id));
    }
});

client.on('ready', () => console.log("=== [Gateway V3.7] 100% 去識別化中樞總控上線！ ==="));
client.login(DISCORD_TOKEN);
