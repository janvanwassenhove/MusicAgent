<template>
  <MainLayout>
    <SongConfiguration @formSubmitted="startEventSource" />
    <hr>
    <div class="d-flex justify-content-between mb-3">
      <button
          class="btn btn-primary"
          :class="{ 'btn-dark-green': visibleDivs.songParameters }"
          @click="toggleVisibility('songParameters')">
        <i class="fas fa-music"></i> Song Parameters
      </button>
      <button
          class="btn btn-primary"
          :class="{ 'btn-dark-green': visibleDivs.agentTimeline }"
          @click="toggleVisibility('agentTimeline')">
        <i class="fas fa-stream"></i> Music Creation Timeline
      </button>
      <button
          class="btn btn-primary"
          :class="{ 'btn-dark-green': visibleDivs.agentConversations }"
          @click="toggleVisibility('agentConversations')">
        <i class="fas fa-comments"></i> Agent Conversations
      </button>
      <button
          class="btn btn-primary"
          :class="{ 'btn-dark-green': visibleDivs.musicAgentLogs }"
          @click="toggleVisibility('musicAgentLogs')" >
        <i class="fas fa-file-alt"></i> Music Agent Logs
      </button>
      <button
          class="btn btn-primary"
          :class="{ 'btn-dark-green': visibleDivs.sonicPiCode }"
          @click="toggleVisibility('sonicPiCode')">
        <i class="fas fa-code"></i> Sonic Pi Code
      </button>
    </div>

    <div class="row">
      <div v-show="visibleDivs.songParameters" class="col-md-6 py-4">
        <SongParameters ref="songParametersRef" />
      </div>
      <div v-show="visibleDivs.agentTimeline" class="col-md-6 py-4">
        <AgentTimeline ref="agentTimelineRef"/>
      </div>
      <div v-show="visibleDivs.agentConversations">
        <AgentConversations ref="agentConversationsRef" />
      </div>
      <div v-show="visibleDivs.musicAgentLogs">
        <MusicAgentLogs />
      </div>
      <div v-show="visibleDivs.sonicPiCode">
        <SonicPiCode ref="sonicPiCodeRef" />
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useStore, mapState, mapMutations } from 'vuex'
import MainLayout from '@/layouts/MainLayout.vue'
import SongConfiguration from '@/components/SongConfiguration.vue'
import AgentTimeline from '@/components/AgentTimeline.vue'
import MusicAgentLogs from '@/components/MusicAgentLogs.vue'
import SonicPiCode from '@/components/SonicPiCode.vue'
import SongParameters from '@/components/SongParameters.vue'
import AgentConversations from '@/components/AgentConversations.vue'

export default {
  name: 'HomePage',
  components: {
    MainLayout,
    SongConfiguration,
    AgentTimeline,
    MusicAgentLogs,
    SonicPiCode,
    SongParameters,
    AgentConversations
  },
  data() {
    return {
      visibleDivs: {
        songParameters: false,
        agentTimeline: false,
        agentConversations: false,
        musicAgentLogs: false,
        sonicPiCode: false
      }
    };
  },
  computed: {
    ...mapState(['formSubmitted', 'formData', 'logMessages', 'songParameters', 'currentPhase', 'completedPhases']),
  },
  methods: {
    ...mapMutations(['setFormSubmitted']),
    toggleVisibility(div) {
      this.visibleDivs[div] = !this.visibleDivs[div];
    }
  },
  setup() {
    const store = useStore()
    console.log("Store in setup:", store)
    const formData = ref(store.state.formData)
    const logMessages = ref(store.state.logMessages || [])
    const currentPhase = ref(store.state.currentPhase)
    const completedPhases = ref(store.state.completedPhases)
    const songParameters = ref(store.state.songParameters)
    const inputPrompt = ref('')
    const inputModal = ref(null)
    const eventSource = ref(null)
    const sonicPiCodeRef = ref(null)
    const agentConversationsRef = ref(null)
    const agentTimelineRef = ref(null)

    const resetCurrentPhase = () => {
      currentPhase.value = ''
      completedPhases.value = []
    }

    const startEventSource = () => {
      store.commit('setFormSubmitted', true);
      if (eventSource.value) {
        eventSource.value.close()
      }
      console.log("EventSource is:", eventSource.value);

      resetCurrentPhase()
      eventSource.value = new EventSource(`${process.env.VUE_APP_API_URL}/api/stream`)

      eventSource.value.onopen = () => {
        console.log("EventSource connection opened")
      }

      eventSource.value.onmessage = (e) => {
        console.log("Received message:", e.data)
        if (store.state.formSubmitted && e.data.includes('"sonicpi_code"')) {
          console.log("Found Sonic pi code in response")
          if (formData.value.song_name && formData.value.song_name.trim() !== '') {
            console.log("Found Sonic pi code in response " + formData.value.song_name)
            sonicPiCodeRef.value?.fetchSonicPiCode(formData.value.song_name);
          }
        }
        if (e.data === "DONE") {
          const completionAlert = document.getElementById('completionAlert')
          completionAlert.style.display = 'block'
          store.commit('setFormSubmitted', false);
          if (formData.value.song_name && formData.value.song_name.trim() !== '') {
            sonicPiCodeRef.value?.fetchSonicPiCode(formData.value.song_name);
          }
        } else if (e.data.startsWith("input_required|")) {
          const [, prompt] = e.data.split("|")
          inputPrompt.value = prompt
          inputModal.value.show()
        } else {
          if (agentConversationsRef.value) {
            agentConversationsRef.value.handleAgentConversations(e);
          } else {
            console.error("agentConversationsRef is null");
          }

          const parameterRegex = /\[([A-Z_]+)\]:\[(.*?)\]/g;
          const paramMatches = [...e.data.matchAll(parameterRegex)];
          console.log("Parameter matches:", paramMatches);

          if (paramMatches.length > 0) {
            paramMatches.forEach(match => {
              const [, key, value] = match;
              songParameters.value[key] = value.trim();
            });
          } else {
            console.log("Received message pushing to logMessages: " + e.data);
            logMessages.value.push(e.data);
            if (agentTimelineRef.value) {
              agentTimelineRef.value.processPhaseStart(e.data);
            } else {
              console.debug("agentTimelineRef is null");
            }
          }
        }
      }

      eventSource.value.onerror = (e) => {
        console.error('EventSource error:', e)
        logMessages.value.push('Error in event stream. Please check server logs.')
        eventSource.value.close()
      }
    }

    onMounted(() => {
      console.log("formSubmitted in Home.vue:", store.state.formSubmitted)
      startEventSource()
    })

    return {
      formData,
      logMessages,
      currentPhase,
      completedPhases,
      inputPrompt,
      inputModal,
      startEventSource,
      sonicPiCodeRef,
      agentConversationsRef,
      agentTimelineRef
    }
  }
}
</script>

<style scoped>
.btn-dark-green {
  background-color: #1A4731 !important;
  border-color: #1A4731 !important;
  color: white !important;
}
</style>
