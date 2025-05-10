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
            <model-selector />
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
          >
            <template #tag="{ option, remove }">
              <div class="multiselect__tag">
                <button
                    @click="togglePlayPause(option)"
                    class="play-pause-button">
                  <i :class="option.isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
                </button>
                <span>{{ option.Filename }}</span>
                <div v-if="isPlaying && currentSample === option.Filename" class="sound-wave">
                  <span></span><span></span><span></span><span></span>
                </div>
                <button @click="remove(option)" class="multiselect__tag-icon">
                  <i class="icon-remove"></i>
                </button>
              </div>
            </template>

          </multiselect>
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
import ModelSelector from '@/components/ModelSelector.vue'
import { mapState } from 'vuex'

export default {
  name: 'CreativeMode',
  components: {
    MainLayout,Multiselect, VisualizationControls, ModelSelector
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
      providers: [],
      availableModels: [],
      selectedFiles: [],
      options: [],
      isLoading: false,
      showSongNameModal: false,
      isEditingSongName: false,

      audio: null,
      currentSample: null,
      isPlaying: false,
      currentTime: 0,
      duration: 0
    };
  },
  computed: {
    ...mapState({
      selectedModel: state => state.formData.selected_model,
      selectedProvider: state => state.formData.api_provider
    }),
    parsedSonicPiCode() {
      return this.sonicPiCode ? this.parseSonicPiCode(this.sonicPiCode) : '';
    }
  },
  methods: {
    async togglePlayPause(option) {
      option.isPlaying = !option.isPlaying;
      if (this.isPlaying && this.currentSample === option.Filename) {
        this.pauseSample();
      } else {
        await this.playSample(option.Filename);
      }
      console.log(`${option.Filename} is now ${option.isPlaying ? 'playing' : 'paused'}`);
    },
    async playSample(filename) {
      if (this.audio && this.currentSample === filename) {
        this.audio.play();
        this.isPlaying = true;
        return;
      }
      if (this.audio) {
        this.audio.pause();
      }
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample/${filename}`, {responseType: 'blob'});
        const url = URL.createObjectURL(response.data);
        this.audio = new Audio(url);

        this.audio.onloadedmetadata = () => {
          this.duration = this.audio.duration;
        };

        this.audio.ontimeupdate = () => {
          this.currentTime = this.audio.currentTime;
        };

        this.audio.onended = () => {
          this.isPlaying = false;
          this.currentSample = null;
          this.audio = null;
          // Find and update the option's isPlaying state
          const option = this.selectedFiles.find(file => file.Filename === filename);
          if (option) {
            option.isPlaying = false;
          }
        };

        this.audio.play();
        this.currentSample = filename;
        this.isPlaying = true;
      } catch (error) {
        console.error('Error playing sample:', error);
      }
    },

    pauseSample() {
      if (this.audio) {
        this.audio.pause();
        this.isPlaying = false;
      }
    },
    // Check if the option is selected
    isSelected(option) {
      return this.selectedFiles.some(selected => selected.Filename === option.Filename);
    },
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
          selected_model: this.selectedModel,
          api_provider: this.selectedProvider
        }, {
          headers: { 'Content-Type': 'application/json' }
        });
        const result = response.data;
        if (result.error) {
          console.info('Error from agent:', result.error);
          await this.refreshSonicPiCode();
        } else {
          this.chatLog.push({ sender: 'Agent', text: result.comment });
          this.selectedFiles = [];
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
.play-pause-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-right: 8px; /* Space between the icon and the filename */
  flex-shrink: 0;
}

.icon-play, .icon-pause {
  font-size: 16px; /* Adjust icon size as needed */
  color: orange;
}

.multiselect__tag {
  display: flex;
  align-items: center;
  position: relative;
  min-height: 24px;
  padding-right: 30px;
}

.multiselect__tag-icon {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;

}

.sound-wave {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 16px;
  margin: 0 8px;
}

.sound-wave span {
  display: inline-block;
  width: 2px;
  height: 100%;
  background-color: #1A4731;
  animation: wave 1s ease-in-out infinite;
}

.sound-wave span:nth-child(2) {
  animation-delay: 0.2s;
}

.sound-wave span:nth-child(3) {
  animation-delay: 0.4s;
}

.sound-wave span:nth-child(4) {
  animation-delay: 0.6s;
}

@keyframes wave {
  0%, 100% { height: 4px; }
  50% { height: 10px; }
}
</style>