const fs = require('fs');
const path = require('path');
const ini = require('ini');
const http = require('http'); // 🔒 換裝官方最鋼鐵、100% 死等位元組落盤的原生網路卡插銷

const configPath = path.join(__dirname, 'config.ini');
const configFile = fs.readFileSync(configPath, 'utf-8');
const config = ini.parse(configFile);

function sendPromptToLLM(recognizedText) {
    const useLocal = config.LLM_SWITCH.USE_LOCAL_OLLAMA === 'true' || config.LLM_SWITCH.USE_LOCAL_OLLAMA === true;
    const systemPrompt = config.LLM_NUANCES.SYSTEM_PROMPT;

    return new Promise((resolve, reject) => {
        if (useLocal) {
            const victusIp = config.OLLAMA_CONFIG.VICTUS_IP;
            const port = parseInt(config.OLLAMA_CONFIG.PORT || 11434);
            const modelName = config.OLLAMA_CONFIG.MODEL_NAME;

            // 📦 構建真空的純 JSON 請求體
            const postData = JSON.stringify({
                model: modelName,
                messages: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: recognizedText }
                ],
                options: { temperature: 0.2 },
                stream: false // 🔒 聽中隊長軍令：關閉打字機，強迫 Ollama 把整句話在內存裡全部榨乾淨！
            });

            const options = {
                hostname: victusIp,
                port: port,
                path: '/api/chat',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                }
            };

            console.log(`[LLM Module] 🏠 REST API Configured -> Dead-waiting for full sentence from http://${victusIp}:${port}/api/chat ...`);

            // 🚀 採用最鋼鐵的原生 HTTP 管道，100% 死等整個數據包全部入閘完畢！
            const req = http.request(options, (res) => {
                let rawBody = '';
                res.setEncoding('utf-8');
                
                // 逐個分片無傷囤積，絕對不提前閉閘
                res.on('data', (chunk) => { rawBody += chunk; });
                
                // 🔥 只有當網路卡明確回報 END（所有數據 100% 完璧歸趙）時，才發動大閉環解析！
                res.on('end', () => {
                    try {
                        const localData = JSON.parse(rawBody);
                        if (localData.message && localData.message.content) {
                            resolve(localData.message.content.trim());
                        } else if (localData.response) {
                            resolve(localData.response.trim());
                        } else {
                            reject(new Error("Ollama 結構異常: " + rawBody));
                        }
                    } catch (e) {
                        reject(new Error("JSON 完整解析踩空: " + e.message + " -> 原始內容: " + rawBody));
                    }
                });
            });

            req.on('error', (e) => reject(e));
            req.write(postData);
            req.end();

        } else {
            // 🌐 雲端通道（保持最基礎的原生協議）
            const restUrl = config.CLOUD_API_CONFIG.API_URL;
            const restModel = config.CLOUD_API_CONFIG.MODEL_NAME;
            const restKey = config.CLOUD_API_CONFIG.API_KEY;

            console.log(`[LLM Module] 🚀 Cloud REST Stream -> [${restUrl}] ...`);

            fetch(restUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${restKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://github.com',
                    'X-Title': 'DCS AI Copilot'
                },
                body: JSON.stringify({
                    model: restModel,
                    messages: [
                        { role: 'system', content: systemPrompt },
                        { role: 'user', content: recognizedText }
                    ],
                    temperature: 0.3
                })
            })
            .then(res => res.json())
            .then(cloudData => {
                if (cloudData.choices && cloudData.choices.length > 0) {
                    resolve(cloudData.choices.message.content.trim());
                } else {
                    reject(new Error("雲端結構異常: " + JSON.stringify(cloudData)));
                }
            })
            .catch(err => reject(err));
        }
    });
}

module.exports = { sendPromptToCloud: sendPromptToLLM };
