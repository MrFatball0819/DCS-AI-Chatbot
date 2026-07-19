// ==========================================
// 🚀 DCS 戰術 AI 副駕駛 - 超導直連純二進位明文版 (brain_linker.js)
// ==========================================
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const ini = require('ini');

const configPath = path.join(__dirname, 'config.ini');
const configFile = fs.readFileSync(configPath, 'utf-8');
const config = ini.parse(configFile);

/**
 * 🚀 核心大殺器：在 D-1581 網關本地將虛擬 WAV Buffer 透過純二進位 stdin 管道沖進 C++ 肚子裡
 * @param {Buffer} wavBuffer - 100% 純內存帶有 44位元組標頭的虛擬 WAV 文件數據
 */
function interpretVoiceLocal(wavBuffer) {
    if (!wavBuffer || !Buffer.isBuffer(wavBuffer)) return;

    const whisperCli = config.GATEWAY.WHISPER_CLI_PATH;
    const whisperModel = config.GATEWAY.WHISPER_MODEL_PATH;
    const threads = config.GATEWAY.THREADS || 4;
    const useLocalOllama = String(config.LLM_SWITCH.USE_LOCAL_OLLAMA).toLowerCase() === 'true';

    console.log(`[Brain Linker] 正在 D-1581 網關本機發動 ${threads} 核 OpenMP C++ 記憶體管道推理...`);

    // 🔒 復刻最成功的實體命令行引數 Facts：-f - 開放標準輸入，讓它強行讀入完整的虛擬 WAV 數據！
    const cmdArgs = ['-m', whisperModel, '-t', threads.toString(), '-nt', '-f', '-'];

    const child = spawn(whisperCli, cmdArgs, {
        stdio: ['pipe', 'pipe', 'pipe'] // 強制命令管道走純二進位明文，拒絕 utf8 轉碼
    });

    let stdoutData = '';
    let stderrData = '';

    child.stdout.on('data', function(data) { stdoutData += data.toString(); });
    child.stderr.on('data', function(data) { stderrData += data.toString(); });

    // 🚀 核心一擊：直接使用二進位原始數據（Buffer 本身就是二進位）暴力傾倒進去，0 轉碼畸變！
    child.stdin.write(wavBuffer);
    child.stdin.end();

    child.on('close', function(code) {
        if (code !== 0) {
            console.log("[Brain Linker Error] 網關本機 Whisper 推理失敗: " + stderrData);
            return;
        }

        const recognizedText = stdoutData.trim();
        console.log(`\n[🚀 D-1581 網關 8核管道識別大成功]: '${recognizedText}'`);
        
        if (!recognizedText) {
            console.log("[Brain Linker] 辨識字串真空為空，取消拋射。");
            return;
        }

        // 統一戰術駕駛艙 Prompt 約束
        const systemPrompt = 
            "You are an expert military AI co-pilot in a fighter jet (DCS World). " +
            "The captain will give you voice commands. You must respond in a short, crisp, professional " +
            "cockpit radio style (max 15 words). If the captain asks for a procedure (like fire, status, failure), " +
            "briefly acknowledge and state the very first critical step. " +
            "At the very end of your response, always include the exact format: [ACTION: YOUR_DECISION_HERE]";

        let targetUrl = "";
        let requestOptions = { method: 'POST', headers: { 'Content-Type': 'application/json' } };

        if (useLocalOllama) {
            const victusIp = config.OLLAMA_CONFIG.VICTUS_IP;
            const ollamaPort = config.OLLAMA_CONFIG.PORT;
            const ollamaModel = config.OLLAMA_CONFIG.MODEL_NAME;
            
            targetUrl = `http://${victusIp}:${ollamaPort}/api/chat`;
            console.log(`[LLM] 正在將文字超導直連拋射給客廳 Ollama [${targetUrl}]...`);

            requestOptions.body = JSON.stringify({
                model: ollamaModel,
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: recognizedText }
                ],
                options: { temperature: 0.2 },
                stream: false
            });
        } else {
            const apiKey = config.OPENAI_CONFIG.API_KEY;
            targetUrl = "https://openai.com";
            console.log(`[LLM] 正在將文字超導直連拋射給雲端 OpenAI API...`);

            requestOptions.headers['Authorization'] = `Bearer ${apiKey}`;
            requestOptions.body = JSON.stringify({
                model: "gpt-4o-mini",
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: recognizedText }
                ],
                temperature: 0.3,
                max_tokens: 80
            });
        }

        fetch(targetUrl, requestOptions)
        .then(res => res.json())
        .then(data => {
            let llmReply = useLocalOllama ? data.message.content.trim() : data.choices.message.content.trim();

            console.log("\n====================================");
            console.log("[🧠 全分布式 LLM 心智推理大成功!]:");
            console.log(`[副駕駛原始台詞]: ${llmReply}`);
            
            let tacticalAction = "STANDBY";
            if (llmReply.includes("[ACTION:")) {
                tacticalAction = llmReply.split("[ACTION:").pop().replace("]", "").trim();
            }
            console.log(`[📋 飛控 Action 鎖定]: ${tacticalAction}`);
            console.log("====================================\n");
        })
        .catch(err => {
            console.log("[LLM Error] 大腦連線失敗: " + err.message);
        });
    });
}

module.exports = { interpretVoiceLocal };
