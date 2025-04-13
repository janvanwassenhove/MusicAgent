<template>
  <MainLayout>
      <div class="row">
        <div class="song-info">
          <img :src="albumImage" alt="Album Cover" class="thumbnail" v-if="albumImage">
          <div v-if="isEditingSongName">
            <input
              v-model="currentSong"
              type="text"
              class="form-control"
              placeholder="Enter song name"
              @blur="saveSongName"
              @keyup.enter="saveSongName"
            />
          </div>
          <h2 v-else @dblclick="editSongName">{{ currentSong }}</h2>
          <button class="toggle-visualization-btn" @click="visibleDivs.visualization = !visibleDivs.visualization">
            <i class="fas fa-eye"></i>
          </button>
        </div>
        <div v-if="visibleDivs.visualization" class="mt-4 col-md-12 mb-5 d-flex flex-column position-relative">
          <VisualizationControls
          :sonicPiCode="sonicPiCode"
          @toggle-layer="toggleLayer" />
        </div>

        <div v-show="visibleDivs.copilotChat" class="col-md-6 d-flex flex-column">
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
            <div class="col-3"><label for="api_provider" class="form-label me-2 m-2">API Provider:</label></div>
            <div class="col-3">
            <select v-model="apiProvider" id="api_provider" class="form-select me-3" @change="updateModelOptions" required>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
            </div>
            <div class="col-2"><label for="selected_model" class="form-label m-2">Model:</label></div>
            <div class="col-4"><select v-model="selectedModel" id="selected_model" class="form-select" required>
              <option v-for="model in availableModels" :key="model" :value="model" v-text="model"></option>
            </select>
            </div>
          </div>
          <multiselect
              v-model="selectedFiles"
              :options="options"
              :multiple="true"
              :taggable="true"
              @search-change="searchSamples"
              label="Filename"
              track-by="Filename"
              tag-placeholder="Add samples"
              placeholder="Search for samples"
          ></multiselect>
          <textarea v-model="chatInput" placeholder="How can I help you create some music ..." class="mt-1 form-control mb-2"></textarea>

          <div class="button-container mb-2 mt-2">
            <button @click="sendMessage" class="btn btn-primary">Perform your magic!</button>
          </div>
        </div>
      </div>
      <div v-show="visibleDivs.sonicPiCode" class="col-md-6 d-flex flex-column">
        <div class="code-container flex-grow-1">
          <button class="copy-icon" title="Copy to clipboard" @click="copyCode"><i class="fas fa-copy"></i></button>
          <button class="send-icon" title="Send to Sonic Pi" @click="sendCodeToSonicPi"><i class="fas fa-play"></i></button>
          <pre class="sonic-pi-code"><code v-html="parsedSonicPiCode"></code></pre>
        </div>
      </div>
    </div>

  </MainLayout>
</template>

<script>
import MainLayout from '@/layouts/MainLayout.vue';
import axios from 'axios';
import Multiselect from 'vue-multiselect';
import VisualizationControls from '@/components/VisualizationControls.vue';

export default {
  name: 'CreativeMode',
  components: {
    MainLayout,Multiselect, VisualizationControls
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

      totalDuration: 60, // will be overwritten in generateVisualization()
      defines: {}, // stores :hook, :acid_bass etc.
      zoomLevel: 1,

      currentSong: this.$route.query.song || 'Untitled',
      albumImage: '',
      apiProvider: 'openai',
      selectedModel: 'gpt-4o-mini',
      availableModels: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
      selectedFiles: [],
      options: [],
      isLoading: false,
      showSongNameModal: false,
      isEditingSongName: false, 
    };
  },
  computed: {
    parsedSonicPiCode() {
      return this.sonicPiCode ? this.parseSonicPiCode(this.sonicPiCode) : '';
    }
  },
  methods: {
    updateTotalDuration(duration) {
      this.totalDuration = duration;
    },
    toggleVisualization() {
      this.visibleDivs.visualization = !this.visibleDivs.visualization;
      console.log('Visualization toggled:', this.visibleDivs.visualization);
    },
    searchSamples(query) {
      axios.get(`${process.env.VUE_APP_API_URL}/api/sample/search`, { params: { query } })
          .then(response => {
            this.options = response.data;
          });
    },
    toggleLayer(index) {
      const idx = this.collapsedLayers.indexOf(index);
      if (idx !== -1) {
        this.collapsedLayers.splice(idx, 1);
      } else {
        this.collapsedLayers.push(index);
      }
    },
    async fetchSonicPiCode(songName) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${songName}`);
        this.sonicPiCode = response.data.sonicpi_code;
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
    async refreshSonicPiCode() {
      const codeResponse = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${this.currentSong}`);
      this.sonicPiCode = codeResponse.data.sonicpi_code;
    },
    sendMessage() {
      if (this.chatInput.trim() === '') return;

      if (this.currentSong === 'Untitled') {
        alert('Please provide a name for your song before proceeding.');
        this.isEditingSongName = true; // Enable editing mode
        return;
      }

      this.chatLog.push({ sender: 'You', text: this.chatInput });
      this.isLoading = true;
      this.sendChatMessage(this.chatInput);
      this.chatInput = '';
    },
    editSongName() {
      this.isEditingSongName = true; // Enable editing mode
    },
    saveSongName() {
      if (this.currentSong.trim() === '') {
        this.currentSong = 'Untitled'; // Revert to default if empty
      }
      this.isEditingSongName = false; // Disable editing mode
    },
   
    async sendChatMessage(message) {
      try {
        const response = await axios.post(`${process.env.VUE_APP_API_URL}/api/chat`, {
          message: message,
          selectedFiles: this.selectedFiles,
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
      this.loadConversationHistory();

      axios.get(`${process.env.VUE_APP_API_URL}/api/songs/${songName}/image`, { responseType: 'blob' })
        .then(response => {
          this.albumImage = URL.createObjectURL(response.data);
        })
        .catch(error => {
          console.debug('Error fetching album image:', error);
          this.albumImage = require('@/assets/images/assistants/Music_Publisher.webp');
        });
    } 
    if (this.currentSong === 'Untitled') {
        this.isEditingSongName = true; // Enable editing mode
    }
  },
};
</script>

<style scoped>
@import "vue-multiselect/dist/vue-multiselect.min.css";

.btn-dark-green {
  background-color: #1A4731 !important;
  border-color: #1A4731 !important;
  color: white !important;
}
.copilot-chat {
  border: 1px solid #ccc;
  padding: 5px;
  border-radius: 5px;
  background-color: #f9f9f9;
}

.button-container {
  display: flex;
  justify-content: center; /* Horizontally center the button */
  align-items: center; /* Vertically center the button */
  margin-top: 10px; /* Optional: Add spacing above the button */
}

.chat-log {
  max-height: 250px;
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

.thumbnail {
  width: 50px;
  height: 50px;
  object-fit: cover;
}
.song-info {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #1A4731;
  margin-bottom: 5px;
  padding-bottom: 5px;
  position: relative;
}
.song-info h2 {
  margin-left: 10px;
}
.toggle-visualization-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #666;
  cursor: pointer;
  transition: color 0.2s ease;
}
.toggle-visualization-btn:hover {
  color: #278156;
}

</style>