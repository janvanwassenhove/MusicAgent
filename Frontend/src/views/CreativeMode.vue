<template>
  <MainLayout>
    <div class="row">
      <div v-show="visibleDivs.copilotChat" class="col-md-6 d-flex flex-column">
        <h3>Copilot Chat</h3>
        <div class="copilot-chat">
            <div class="chat-log mt-3 overflow-auto border rounded bg-white p-3" style="height: 22.5em; line-height: 1.5em;">
                <div v-for="(message, index) in chatLog" :key="index" class="chat-message">
              <strong>{{ message.sender }}:</strong> {{ message.text }}
            </div>
          </div>
            <textarea v-model="chatInput" placeholder="Type your message here..." class="form-control mb-2"></textarea>
          <button @click="sendMessage" class="btn btn-primary">Send</button>

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
      },
      chatInput: '',
      chatLog: [],
      sonicPiCode: '// Sonic Pi song code will appear here...',
    };
  },
  computed: {
    parsedSonicPiCode() {
      return this.sonicPiCode ? this.parseSonicPiCode(this.sonicPiCode) : '';
    },
  },
  methods: {
    async fetchSonicPiCode(songName) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/get_sonicpi_code/${songName}`);
        this.sonicPiCode = response.data.sonicpi_code;
      } catch (error) {
        console.error('Error fetching Sonic Pi code:', error);
        this.sonicPiCode = '// Failed to load Sonic Pi code.';
      }
    },
    sendMessage() {
      if (this.chatInput.trim() === '') return;
      this.chatLog.push({ sender: 'You', text: this.chatInput });
      this.chatLog.push({ sender: 'Copilot', text: 'Response to: ' + this.chatInput });
      this.chatInput = '';
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
  },
  mounted() {
    const songName = this.$route.query.song;
    if (songName) {
      this.fetchSonicPiCode(songName);
    }
  },
};
</script>

<style scoped>
.btn-dark-green {
  background-color: #1A4731 !important;
  border-color: #1A4731 !important;
  color: white !important;
}
.copilot-chat, .code-container {
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 5px;
  background-color: #f9f9f9;
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
  margin-bottom: 5px;
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
</style>