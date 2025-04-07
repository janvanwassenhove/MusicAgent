<template>
  <MainLayout>
      <div class="row">

      <div v-show="visibleDivs.copilotChat" class="col-md-6 d-flex flex-column">
        <h3>Music Agent Chat</h3>
        <div class="copilot-chat flex-grow-1">
          <div class="chat-log overflow-auto border rounded bg-white p-3" style="min-height: 200px;">
            <div v-for="(message, index) in chatLog" :key="index" class="chat-message d-flex align-items-start mb-3">
              <div v-if="message.sender === 'Agent'" class="d-flex flex-row-reverse align-items-start w-100">
                <img
                    :src="require('@/assets/images/assistants/Artist.webp')"
                    @error="handleImageError"
                    :alt="message.sender"
                    class="chat-image ms-3"
                />
                <div class="chat-text p-3 rounded">
                  <em>{{ message.text }}</em>
                </div>
              </div>
              <div v-else class="d-flex align-items-start">
                <img
                    :src="require('@/assets/images/assistants/Unknown.webp')"
                    @error="handleImageError"
                    :alt="message.sender"
                    class="chat-image me-3"
                />
                <div class="chat-text p-3 rounded">
                  <em>{{ message.text }}</em>
                </div>
              </div>
            </div>
            <div v-if="isLoading" class="loader-container">
              <div class="spinner"></div>
              <div class="loader-text">Magical song creation at work ...</div>
            </div>
          </div>
          <div class="mb-2 d-flex align-items-center mt-2">
            <div class="col-4"><label for="api_provider" class="form-label me-2">API Provider:</label></div>
            <div class="col-8">
            <select v-model="apiProvider" id="api_provider" class="form-select me-3" @change="updateModelOptions" required>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
            </div>
          </div>
          <div class="mb-2 d-flex align-items-center">
            <div class="col-4"><label for="selected_model" class="form-label">Model:</label></div>
            <div class="col-8"><select v-model="selectedModel" id="selected_model" class="form-select" required>
              <option v-for="model in availableModels" :key="model" :value="model" v-text="model"></option>
            </select>
            </div>
          </div>
          <textarea v-model="chatInput" placeholder="Type your message here..." class="mt-1 form-control mb-2"></textarea>
          <button @click="sendMessage" class="btn btn-primary">Perform some magic!</button>
        </div>
      </div>
      <div v-show="visibleDivs.sonicPiCode" class="col-md-6 d-flex flex-column">
        <h3>Sonic Pi Code</h3>
        <div class="code-container flex-grow-1">
          <button class="copy-icon" title="Copy to clipboard" @click="copyCode"><i class="fas fa-copy"></i></button>
          <button class="send-icon" title="Send to Sonic Pi" @click="sendCodeToSonicPi"><i class="fas fa-play"></i></button>
          <pre class="sonic-pi-code"><code v-html="parsedSonicPiCode"></code></pre>
        </div>
      </div>

      <div v-show="visibleDivs.visualization" class="mt-4 col-md-12 d-flex flex-column position-relative">
          <h3>Timeline</h3>

          <div class="controls mb-2">
            <!-- Align icons to the right -->
            <div class="time-scale-icons">
              <button
                :class="['time-scale-btn', { active: timeScale === 'seconds' }]"
                @click="setTimeScale('seconds')"
                title="Seconds"
              >
                <i class="fas fa-clock"></i>
              </button>
              <button
                :class="['time-scale-btn', { active: timeScale === 'milliseconds' }]"
                @click="setTimeScale('milliseconds')"
                title="Milliseconds"
              >
                <i class="fas fa-stopwatch"></i>
              </button>
              <button
                :class="['time-scale-btn', { active: timeScale === 'beats' }]"
                @click="setTimeScale('beats')"
                title="Beats (4 bars)"
              >
                <i class="fas fa-music"></i>
              </button>
            </div>
          </div>

          <div class="visualization-container">
            <div class="timeline-row">
              <div class="layer-name"></div>
              <div class="layer-track timeline-track">
                <div
                    v-for="i in 20"
                    :key="'tick-' + i"
                    class="timeline-tick"
                    :style="{ left: ((i - 1) * 5) + '%' }"
                >
                  &nbsp;{{ formatTickLabel((i - 1) * (totalDuration / 20), 1) }}
                </div>
              </div>
            </div>
            <div
                v-for="(layer, index) in visualizationLayers"
                :key="'layer-' + index"
                class="visualization-row"
            >
              <div class="layer-name" @click="toggleLayer(index)">
                {{ layer[0]?.name }}
              </div>
              <div class="layer-track">
                <div
                    v-for="(segment, segIndex) in layer"
                    :key="segIndex"
                    :class="['segment-wrapper']"
                    :style="segment.style"
                >
                  <div
                      :class="['segment', segment.class, segment.fxClass, segment.infinite ? 'infinite-loop' : '']"
                  >
                    {{ segment.label }}
                    <div class="custom-tooltip-wrapper">
                      <div class="custom-tooltip" v-html="segment.tooltip"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  </MainLayout>
</template>

<script>
import MainLayout from '@/layouts/MainLayout.vue';
import axios from 'axios';

export default {
  name: 'CreativeMode',
  components: {
    MainLayout,
  },
  data() {
    return {
      visibleDivs: {
        copilotChat: true,
        sonicPiCode: true,
        visualization: true,
      },
      chatInput: '',
      chatLog: [],
      sonicPiCode: '// Sonic Pi song code will appear here...',
      visualizationLayers: [],
      playbackTime: 0,
      isPlaying: false,
      totalDuration: 60, // will be overwritten in generateVisualization()
      defines: {}, // stores :hook, :acid_bass etc.
      zoomLevel: 1,
      timeScale: 'seconds', // 'seconds', 'milliseconds', or 'beats'
      collapsedLayers: [],
      currentSong: this.$route.query.song || 'Untitled',
      apiProvider: 'openai',
      selectedModel: 'gpt-4o-mini',
      availableModels: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],

    };
  },
  computed: {
    parsedSonicPiCode() {
      return this.sonicPiCode ? this.parseSonicPiCode(this.sonicPiCode) : '';
    }
  },
  methods: {
    
    toggleLayer(index) {
      const idx = this.collapsedLayers.indexOf(index);
      if (idx !== -1) {
        this.collapsedLayers.splice(idx, 1);
      } else {
        this.collapsedLayers.push(index);
      }
    },
    formatTickLabel(value) {
      switch (this.timeScale) {
        case 'milliseconds':
          return `${(value * 1000).toFixed(0)}ms`;
        case 'beats':
          return `${(value / 60 * 130 / 4).toFixed(1)} bars`; // assuming BPM=130
        default:
          return `${value.toFixed(1)}s`;
      }
    },
    setTimeScale(scale) {
      this.timeScale = scale;
    },
    async fetchSonicPiCode(songName) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${songName}`);
        this.sonicPiCode = response.data.sonicpi_code;
        this.generateVisualization();
      } catch (error) {
        console.error('Error fetching Sonic Pi code:', error);
        this.sonicPiCode = '// Failed to load Sonic Pi code.';
      }
    },
    parseSonicPiCode(code) {
      const keywordRegex = /\b(live_loop|play|sleep)\b/g;
      const numberRegex = /\b\d+(\.\d+)?\b/g;
      const functionRegex = /(:\w+)/g;
      const doendRegex = /\b(do|end)\b/g;

      code = code.replace(keywordRegex, '<span class="keyword">$&</span>');
      code = code.replace(numberRegex, '<span class="number">$&</span>');
      code = code.replace(functionRegex, '<span class="function">$&</span>');
      code = code.replace(doendRegex, '<span class="doend">$&</span>');

      return code;
    },
    copyCode() {
      const codeText = this.sonicPiCode;
      navigator.clipboard.writeText(codeText).then(() => {
        alert('Sonic Pi Code copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy the Sonic Pi code: ', err);
      });
    },
    sendCodeToSonicPi() {
      const codeText = this.sonicPiCode;
      const songName = this.$route.query.song || 'Untitled';
      const agentType = 'mITyJohn';

      axios.post(`${process.env.VUE_APP_API_URL}/api/send_to_sonicpi`, {
        code: codeText,
        song_name: songName,
        agent_type: agentType,
      })
      .then(response => {
        console.info('Code sent to Sonic Pi: ' + response.data.message);
      })
      .catch(error => {
        console.error('Error sending code to Sonic Pi:', error);
        alert('Failed to send the code to Sonic Pi, did you run SonicPi/Setup/recording.rb in Sonic Pi?');
      });
    },
    estimateDuration(lines) {
      return lines.reduce((sum, line) => {
        const match = line.match(/sleep\s+([\d.]+)/);
        return sum + (match ? parseFloat(match[1]) : 0);
      }, 0);
    },
    generateVisualization() {
      const lines = this.sonicPiCode.split('\n');
      const layersMap = new Map();
      const threads = [];
      const loopStartTimes = {};
      this.defines = {};
      let totalDuration = 0;
      let currentThread = null;
      const threadStack = [];
      const fxStack = [];
      let globalTime = 0;
      let liveLoopBodies = {};

      // Determine total duration based on sleep in top-level context only
      lines.forEach((line) => {
        if (!currentThread) {
          const match = line.match(/sleep\s+([\d.]+)/);
          if (match) globalTime += parseFloat(match[1]);
        }
      });
      totalDuration = Math.max(globalTime, 1);
      this.totalDuration = totalDuration;
  
      for (const [loopName, bodyLines] of Object.entries(liveLoopBodies)) {
        const containsStop = bodyLines.some(l => /\bstop\b/.test(l));
        const durationPerIteration = this.estimateDuration(bodyLines) || 4;
        const iterations = Math.floor(this.totalDuration / durationPerIteration);
        const layer = layersMap.get(loopName) || [];

        for (let i = 0; i < iterations; i++) {
          layer.push({
            start: i * durationPerIteration,
            duration: durationPerIteration,
            label: loopName
          });
          if (containsStop) break;
        }
        layersMap.set(loopName, layer);
      }

      globalTime = 0; // reset for second pass
 
      lines.forEach((line, lineIndex) => {
    
        const trimmed = line.trim();
        const liveLoopMatch = trimmed.match(/live_loop\s+(:\w+)/);
        const inThreadMatch = trimmed.match(/in_thread\s+do/);
        const syncMatch = trimmed.match(/sync\s+:?([\w]+)/);
        const sleepMatch = trimmed.match(/sleep\s+([\d.]+)/);
        
        const endMatch = trimmed.match(/\bend\b/);
        const withFxMatch = trimmed.match(/with_fx\s+:?(\w+)/);
        const defineMatch = trimmed.match(/define\s+:?(\w+)/);

        if (defineMatch) {
          const name = defineMatch[1];
          this.defines[name] = true;
        } else if (liveLoopMatch) {
          const name = liveLoopMatch[1].replace(':', '');
          currentThread = {
            name,
            startTime: globalTime,
            currentTime: 0,
            fx: [...fxStack],
            class: 'live-loop',
            index: lineIndex,
            nestingLevel: 0, // Track nesting level
          };
          threads.push(currentThread);
          threadStack.push(currentThread);
        } else if (inThreadMatch) {
          const parent = currentThread;
          const start = parent ? parent.currentTime : globalTime;
          currentThread = {
            name: `in_thread_${threads.length}`,
            startTime: start,
            currentTime: 0,
            fx: [...fxStack],
            class: 'in-thread',
            index: lineIndex,
            nestingLevel: 0, // Track nesting level
          };
          threads.push(currentThread);
          threadStack.push(parent);
        } else if (withFxMatch) {
          fxStack.push(withFxMatch[1]);
        } else if (syncMatch && currentThread) {
          const target = syncMatch[1];
          const syncTime = loopStartTimes[target] ?? 0;
          currentThread.startTime += syncTime;
        } else if (sleepMatch) {
          const duration = parseFloat(sleepMatch[1]);
          if (currentThread) {
            currentThread.currentTime += duration;
          } else {
            globalTime += duration;
          }
        } else if (trimmed.endsWith('do')) {
          // Increment nesting level for nested blocks
          if (currentThread) {
            currentThread.nestingLevel++;
          }
        } else if (endMatch) {
          if (currentThread) {
            if (currentThread.nestingLevel > 0) {
              // Decrement nesting level for nested blocks
              currentThread.nestingLevel--;
            } else {
              // Finalize the current thread when nesting level reaches 0
              const duration = currentThread.currentTime;
              const name = currentThread.name;
              loopStartTimes[name] = currentThread.startTime;

              const fxClass = currentThread.fx.length > 0 ? `fxClass-${currentThread.fx[0]}` : '';
              const codeSnippet = this.parseSonicPiCode(
                lines.slice(currentThread.index, lineIndex + 1).join('\n') // Include the current line with `end`
              );
              const tooltip = `
                <h6>${name}</h6>
                <ul>
                  <li>FX: ${currentThread.fx.join(', ') || 'none'}</li>
                  <li>Duration: ${duration}s</li>
                </ul>
                <pre class="sonic-pi-code"><code>${codeSnippet}</code></pre>
              `;

              layersMap.set(name, [{
                name,
                label: name,
                class: currentThread.class,
                fxClass,
                tooltip,
                infinite: false,
                style: `left: ${(currentThread.startTime / totalDuration) * 100}%; width: ${(duration / totalDuration) * 100}%;`
              }]);

              currentThread = threadStack.pop() || null;
            }
          }
        }
      });

      threads.forEach(thread => {
        if (!layersMap.has(thread.name)) {
          const duration = this.totalDuration - thread.startTime;
          const fxClass = thread.fx.length > 0 ? `fxClass-${thread.fx[0]}` : '';
          const tooltip = `${thread.name}\nFX: ${thread.fx.join(', ') || 'none'}\nDuration: ∞`;

          layersMap.set(thread.name, [{
            name: thread.name,
            label: thread.name,
            class: thread.class,
            fxClass,
            tooltip,
            infinite: true,
            style: `left: ${(thread.startTime / this.totalDuration) * 100}%; width: ${(duration / this.totalDuration) * 100}%;`
          }]);
        }
      });

      const sortedLayers = Array.from(layersMap.entries())
          .sort((a, b) => {
            const aIndex = threads.find(t => t.name === a[0])?.index ?? 0;
            const bIndex = threads.find(t => t.name === b[0])?.index ?? 0;
            return aIndex - bIndex;
          })
          .map(entry => entry[1]);

      this.visualizationLayers = sortedLayers;
    },

    async refreshSonicPiCode() {
      const codeResponse = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${this.currentSong}`);
      this.sonicPiCode = codeResponse.data.sonicpi_code;
    },
    sendMessage() {
      if (this.chatInput.trim() === '') return;
      this.chatLog.push({ sender: 'You', text: this.chatInput });
      this.isLoading = true;
      this.sendChatMessage(this.chatInput);
      this.chatInput = '';
    },
    async sendChatMessage(message) {
      try {
        const response = await axios.post(`${process.env.VUE_APP_API_URL}/api/chat`, {
          message: message,
          song_name: this.currentSong,
          agent_type: this.selectedAgent,
          selected_model: this.model,
          api_provider: this.apiProvider
        }, {
          headers: { 'Content-Type': 'application/json' }
        });
        const result = response.data;
        if (result.error) {
          console.info('Error from agent:', result.error);
          await this.refreshSonicPiCode();
        } else {
          this.chatLog.push({ sender: 'Agent', text: result.comment });
          await this.refreshSonicPiCode();
        }
        this.isLoading = false;
      } catch (error) {
        console.error('Error sending chat message:', error);
      } finally {
        this.isLoading = false;
      }
    },
    handleImageError(event) {
      event.target.src = require('@/assets/images/assistants/Unknown.webp');
    },
    updateModelOptions() {
      if (this.apiProvider === 'openai') {
        this.availableModels = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'];
      } else if (this.apiProvider === 'anthropic') {
        this.availableModels = ['claude-v1', 'claude-v1.2', 'claude-instant-v1'];
      }
    },
    async loadConversationHistory() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/conversation_history`, {
          params: { song_name: this.currentSong }
        });
        this.chatLog = response.data.map(entry => ({
          sender: entry.role === 'user' ? 'You' : 'Agent',
          text: entry.content
        }));
      } catch (error) {
        console.error('Error loading conversation history:', error);
      }
    }
  },
  mounted() {
    const songName = this.$route.query.song;
    if (songName) {
      this.fetchSonicPiCode(songName);
    }
    this.loadConversationHistory();
  },
};
</script>

<style scoped>
.btn-dark-green {
  background-color: #1A4731 !important;
  border-color: #1A4731 !important;
  color: white !important;
}
.copilot-chat {
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 5px;
  background-color: #f9f9f9;
}

.code-container {

}

.chat-log {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ddd;
  padding: 10px;
  border-radius: 5px;
  background-color: #fff;
}
.chat-message {
  display: flex;
  align-items: start;
  margin-bottom: 1rem;
}
.chat-image {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 1rem;
}

.chat-text {
  background-color: #f1f1f1;
  padding: 1rem;
  border-radius: 0.5rem;
}
.sonic-pi-code {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 5px;
  white-space: pre-wrap;
  max-height: 600px;
  overflow-y: auto;
}
.keyword {
  color: #d73a49;
  font-weight: bold;
}
.number {
  color: #005cc5;
}
.function {
  color: #6f42c1;
}
.doend {
  color: #d73a49;
  font-weight: bold;
}
.copy-icon, .send-icon {
  margin-right: 10px;
  cursor: pointer;
}
.visualization-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}
.visualization-row {
  display: flex;
  align-items: center;
}
.timeline-row {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 4px;
}
.timeline-track {
  position: relative;
  height: 16px;
  background: transparent;
  flex: 1;
}
.timeline-tick {
  position: absolute;
  top: 0;
  height: 100%;
  width: 1px;
  border-left: 1px dashed #bbb;
  font-size: 0.65rem;
  text-align: left;
  transform: translateX(-1px);
  white-space: nowrap;
}
.layer-name {
  width: 120px;
  font-weight: bold;
  font-size: 0.85rem;
  text-align: right;
  margin-right: 8px;
  color: #333;
}
.layer-track {
  position: relative;
  flex: 1;
  height: 24px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow: visible;
}
.segment-wrapper {
  position: absolute;
  height: 100%;
  top: 0;
}
.segment {
  height: 100%;
  border-radius: 3px;
  text-align: center;
  font-size: 0.75rem;
  color: #9c1c1c;
  padding: 0 4px;
  white-space: nowrap;
  overflow: visible;
  text-overflow: ellipsis;
  position: relative;
  cursor: pointer;
}
.live-loop { background-color: #3a86ff; }
.in-thread { background-color: #ff006e; }
.fxClass-reverb { border: 2px dashed #aaa; }
.fxClass-distortion { border: 2px solid red; }
.infinite-loop {
  opacity: 0.7;
  background: linear-gradient(to right, #888 70%, transparent 100%);
}
.custom-tooltip-wrapper {
  position: absolute;
  top: 100%;
  left: 0;
  display: none;
  z-index: 100;
}
.segment:hover .custom-tooltip-wrapper {
  display: block;
}
.custom-tooltip {
  background-color: #fff;
  color: #000;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  text-align: left;
  font-size: 0.75rem;
  max-width: 500px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}
.keyword { color: #d73a49; font-weight: bold; }
.number { color: #005cc5; }
.function { color: #6f42c1; }
.doend { color: #22863a; font-style: italic; }

.time-scale-icons {
  display: flex;
  gap: 8px;
  justify-content: flex-end; /* Align icons to the right */
}

.time-scale-btn {
  background: none;
  border: none;
  font-size: 1.2rem; /* Make icons slightly smaller */
  color: #666;
  cursor: pointer;
  transition: color 0.2s ease;
}

.time-scale-btn.active {
  color: #1A4731;
}

.time-scale-btn:hover {
  color: #278156;
}

.loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 10px;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #000;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loader-text {
  margin-top: 5px;
  font-size: 1rem;
  color: #666;
}
</style>