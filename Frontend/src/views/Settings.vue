<!-- Filename: Settings.vue -->
<template>
  <MainLayout>
    <div class="container">
      <h1>Settings</h1>
      <p>Configure your Music Agent settings here.</p>
      <ul class="nav nav-tabs" id="settingsTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="general-tab" data-bs-toggle="tab" data-bs-target="#general" type="button" role="tab" aria-controls="general" aria-selected="true">General</button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="sonicpi-tab" data-bs-toggle="tab" data-bs-target="#sonicpi" type="button" role="tab" aria-controls="sonicpi" aria-selected="false">Sonic Pi Configuration</button>
        </li>
      </ul>
      <div class="tab-content" id="settingsTabsContent">
        <div class="tab-pane fade show active" id="general" role="tabpanel" aria-labelledby="general-tab">
          <h4>Artist Configuration</h4>
          <form @submit.prevent="updateArtistConfig">
            <div class="col-md-5 mt-3 mb-3">
              <label for="artistSelect" class="form-label">Select Artist:</label>
              <select id="artistSelect" v-model="selectedArtist" class="form-select" @change="updateArtistConfigFields" required>
                <option v-for="type in artists" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
            <div class="mb-3">
              <label for="artistStyle" class="form-label">Artist Style (<i>Styling is used for e.g. album cover creation</i>):</label>
              <textarea id="artistStyle" v-model="artistConfig.artist_style" class="form-control" rows="4" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Update Artist Configuration</button>
          </form>
        </div>
        <div class="tab-pane fade" id="sonicpi" role="tabpanel" aria-labelledby="sonicpi-tab">
          <h4>Sonic Pi Configuration</h4>
          <div class="row col-md-12 ">
            <div class="row col-md-10  mb-3">
              <div class="col-md-5 ">
                <label for="sonicPiIP" class="form-label">Local IP:</label>
                <input type="text" id="sonicPiIP" v-model="sonicPiConfig.sonic_pi_IP" class="form-control" />
              </div>
              <div class="col-md-5 ">
                <label for="sonicPiPort" class="form-label">Incoming OSC Port:</label>
                <input type="number" id="sonicPiPort" v-model="sonicPiConfig.sonic_pi_port" class="form-control" />
              </div>
            </div>
            <div class="mt-3">
              <button @click="updateSonicPiConfig" class="btn btn-primary">Update Configuration</button>
            </div>
            <hr class="mt-3">
            <p>
              Sonic Pi incoming OSC port and local IP address is used for playback by Music Agent.
              During Song Creation, when applying playback, please ensure having following code launched in Sonic Pi to capture OSC messages from Music Agent.
            </p>
            <div class="sonic-pi-code py-4 code-container">
              <pre><code>
              <span class="keyword">live_loop</span> <span class="function">:listen</span> <span class="doend">do</span>
                use_real_time
                script = sync "/osc*/run-code"
                begin
                  eval script[<span class="number">0</span>]
                  osc_send '<span class="number">{{ sonicPiHost }}</span>', <span class="number">{{ sonicPiPort }}</span>, '/feedback', 'MusicAgent Code was executed successfully'
                  rescue Exception => e<br>
                osc_send '<span class="number">{{ sonicPiHost }}</span>', <span class="number">{{ sonicPiPort }}</span>, '/feedback'
                <span class="doend">end</span>
              <span class="doend">end</span>
              </code></pre>
            </div>
          </div>

        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import MainLayout from "@/layouts/MainLayout.vue";
import { mapMutations } from 'vuex';
import axios from 'axios';

export default {
  name: 'AgentSettings' ,
  components: {MainLayout},
  data() {
    return {
      sonicPiHost: '127.0.0.1',
      sonicPiPort: 4559,
      visibleDivs: {
        songParameters: false,
        agentTimeline: false,
        agentConversations: false,
        musicAgentLogs: false,
        sonicPiCode: false
      },
      sonicPiConfig: {
        sonic_pi_IP: '',
        sonic_pi_port: ''
      },
      artistConfig: {
        artist_style: '',
        agent_name: ''
      },
      agentTypes: [],
      selectedAgentType: 'mITyJohn',
      artists: [],
      selectedArtist: null
    };
  },
  methods: {
    ...mapMutations(['setFormSubmitted']),
    toggleVisibility(div) {
      this.visibleDivs[div] = !this.visibleDivs[div];
    },
    async loadSonicPiConfig() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sonicpi/config`);
        this.sonicPiHost = response.data.sonic_pi_IP;
        this.sonicPiPort = response.data.sonic_pi_port;
      } catch (error) {
        console.error('Error loading Sonic Pi config:', error);
      }
    },
    async updateArtistConfig() {
      try {
        // Assuming you have an API endpoint to update the artist configuration
        await fetch(`${process.env.VUE_APP_API_URL}/api/artist_config`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.artistConfig)
        });
        alert('Artist configuration updated successfully');
      } catch (error) {
        console.error('Error updating artist configuration:', error);
      }
    },

    async fetchSonicPiConfig() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sonicpi/config`)
        this.sonicPiConfig = response.data
      } catch (error) {
        console.error('Error fetching Sonic Pi config:', error)
      }
    },
    async updateSonicPiConfig() {
      try {
        const response = await axios.post(
            `${process.env.VUE_APP_API_URL}/api/sonicpi/config`,
            this.sonicPiConfig
        )
        if (response.data.message) {
          alert('Configuration updated successfully')
        }
      } catch (error) {
        console.error('Error updating Sonic Pi config:', error)
        alert('Failed to update configuration')
      }
    },
    async fetchAgentTypes() {
      try {
        const response = await fetch(`${process.env.VUE_APP_API_URL}/api/agent_types`);
        const data = await response.json();
        this.agentTypes = data.agent_types;
        this.artists = data.agent_types;
      } catch (error) {
        console.error('Error fetching agent types:', error);
      }
    },
    async updateArtistConfigFields() {
      if (!this.selectedArtist) return;

      try {
        const response = await fetch(`${process.env.VUE_APP_API_URL}/api/artists/config`);
        const data = await response.json();
        const selectedConfig = data.find(config => config.agent_type === this.selectedAgentType);

        if (selectedConfig) {
        this.artistConfig.agent_name = selectedConfig.agent_name || '';
        this.artistConfig.artist_style = selectedConfig.artist_style || '';
        } else {
          // If no config found, reset to empty
          this.artistConfig.agent_name = '';
          this.artistConfig.artist_style = '';
        }
      } catch (error) {
        console.error('Error fetching Artist config for selected agent type:', error);
        this.artistConfig.agent_name = '';
        this.artistConfig.artist_style = '';
      }
    },
    async updateSonicPiConfigFields() {
      // Fetch the Sonic Pi config for the selected agent type
      try {
        const response = await fetch(`${process.env.VUE_APP_API_URL}/api/sonicpi/config`);
        const data = await response.json();
        const selectedConfig = data.find(config => config.agent_type === this.selectedAgentType);

        if (selectedConfig) {
          this.sonicPiConfig.ip = selectedConfig.sonic_pi_IP || '';
          this.sonicPiConfig.port = selectedConfig.sonic_pi_port || '';
        } else {
          // If no config found, reset to empty
          this.sonicPiConfig.ip = '';
          this.sonicPiConfig.port = '';
        }
      } catch (error) {
        console.error('Error fetching Sonic Pi config for selected agent type:', error);
        this.sonicPiConfig.ip = '';
        this.sonicPiConfig.port = '';
      }
    },
  },
  mounted() {
    this.fetchSonicPiConfig();
    this.fetchAgentTypes();
    this.loadSonicPiConfig();
  }

}
</script>

<style scoped>

/* Add any specific styles for the settings view here */
.nav-tabs {
  border-bottom: 1px solid #1A4731;
  border-radius: 5px;
  border-bottom-left-radius: 0px;
}

.nav-tabs .nav-item {
  margin-bottom: -1px;
}

.nav-tabs .nav-link {
  border: 1px solid transparent ;
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
  color: #FFA500;
  font-weight: bold;
}

.nav-tabs .nav-link:hover {
  border-color: #e9ecef #e9ecef #ddd;
}

.nav-tabs .nav-link.active {
  color: #111;
  background-color: #fff;
  border-color: #1A4731 #1A4731 #fff;
}

.tab-content {
  border: 1px solid #1A4731;
  border-top: none;
  padding: 1rem;
  background-color: #fff;
  border-radius: 5px;
  border-top-left-radius: 0px;
}

</style>
