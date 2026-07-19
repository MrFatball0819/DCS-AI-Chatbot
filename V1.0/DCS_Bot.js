// ==========================================
// 🚀 DCS 戰術 AI 副駕駛 - 全記憶體超導直連總控中心 (DCS_Bot.js)
// ==========================================
const { Client, GatewayIntentBits } = require('discord.js');
const { joinVoiceChannel, VoiceConnectionStatus } = require('@discordjs/voice');
const prism = require('prism-media');
const path = require('path'); 
const fs = require('fs');
const ini = require('ini');

// 🔒 100% 動態相對路徑鎖定同級 config.ini
const configPath = path.join(__dirname, 'config.ini');
const configFile = fs.readFileSync(configPath, 'utf-8');
const config = ini.parse(configFile);

const DISCORD_TOKEN = config.DISCORD.BOT_TOKEN;

// 🔒 引入同級相對 DSP 處理模組
const dsp = require('./dsp_processor.js');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildVoiceStates,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

let audioChunks = [];
let opusStream = null;
let pcmDecoder = null;

function setupVoiceReceiver(connection, targetHenryId) {
    console.log(`[Gateway] 純內存超導直連管線就位。唯一監聽對象 ID: ${targetHenryId}`);

    // 🟢 狀態一：Henry 按下 PTT (頭像亮綠圈)
    connection.receiver.speaking.on('start', function(userId) {
        if (userId !== targetHenryId) return;
        
        console.log("\n🟢 === [PTT ON] Henry 開始發言，記憶體水閘開啟... ===");
        audioChunks = []; 

        opusStream = connection.receiver.subscribe(userId, { mode: 'opus' });
        pcmDecoder = new prism.opus.Decoder({ rate: 48000, channels: 2, frameSize: 960 });

        opusStream.pipe(pcmDecoder);
        pcmDecoder.on('data', function(chunk) {
            audioChunks.push(chunk);
        });
    });

    // 🔴 狀態二：Henry 放開 PTT (頭像綠圈熄滅)
    connection.receiver.speaking.on('end', function(userId) {
        if (userId !== targetHenryId) return;
        if (!opusStream) return;

        console.log("🔴 === [PTT OFF] Henry 閉嘴。正在發動【純記憶體】DSP 結算... ===");

        // 斷開進站水閘流
        opusStream.destroy();
        if (pcmDecoder) pcmDecoder.destroy();
        opusStream = null;
        pcmDecoder = null;

        // 🚀 核心咬合：呼叫 DSP 模組在記憶體中產出 100% 乾淨帶有 44位元組標頭的虛擬 WAV Buffer
        const finalMemoryWav = dsp.processAudioInMemory(audioChunks);

        if (finalMemoryWav) {
            console.log(`[Network] 正在將純內存 WAV (${finalMemoryWav.length} 位元組) 超導射入網關本地 Python 大腦...`);
            
            // 🚀 直接將 Buffer 透過本地 HTTP (Loopback 127.0.0.1) 拋射給常駐在本機背景的 local_brain.py
            fetch('http://localhost:5002/whisper', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'audio/wav', 
                    'Content-Length': finalMemoryWav.length 
                },
                body: finalMemoryWav
            })
                        // 🚀 終極修正：必須加上 return！強迫 Node.js 將解析完的 JSON 物件往下傳遞，徹底推平 undefined 幽靈！
            .then(res => { 
                return res.json(); 
            })
            .then(data => {
                console.log("\n====================================");
                console.log("[🧠 全分布式超導直連大成功!]:");
                console.log(`[🚀 聽到 Henry 指令]: '${data.text}'`);
                console.log(`[🎙️ 副駕駛戰術台詞]: '${data.reply}'`);
                console.log(`[📋 最終飛控 Action ]: [ACTION: ${data.action}]`);
                console.log("====================================\n");
            })
            .catch(err => {
                console.log("[Network Error] 網關本地 Python 大腦 (local_brain.py) 未拉起或假死: " + err.message);
            });
        }
    });
}

// 監聽一鍵通車指令
client.on('messageCreate', function(message) {
    if (message.author.bot) return;

    if (message.content === '!join') {
        const voiceChannel = message.member.voice.channel;
        if (!voiceChannel) return;

        console.log(`[Gateway] 收到一鍵通車指令！自動咬合目標頻道: ${voiceChannel.name}`);

        const connection = joinVoiceChannel({
            channelId: voiceChannel.id,
            guildId: message.guild.id,
            adapterCreator: message.guild.voiceAdapterCreator,
            selfDeaf: false,
            selfMute: true
        });

        connection.on(VoiceConnectionStatus.Ready, function() {
            console.log("[Gateway] 大閘全線貫通。音訊雙向對齊完畢。");
            setupVoiceReceiver(connection, message.author.id);
        });
    }
});

client.on('ready', function() { console.log("=== [Gateway] Bot 依據 config.ini 成功上線！ ==="); });
client.login(DISCORD_TOKEN);
