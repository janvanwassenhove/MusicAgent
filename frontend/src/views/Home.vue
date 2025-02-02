<template>

  <div class="text-center py-2 mb-2" style="background-color: #1A4731;">
    <img src="@/assets/images/musicagent.png" alt="MusicAgent" style="max-width: 100%; height: 200px;">
  </div>
  <div class="container main_container p-4">
    <SongConfiguration @formSubmitted="startEventSource" />
    <hr>
    <div class="d-flex justify-content-between mb-3">
      <button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#songParameters" aria-expanded="true" aria-controls="songParameters">
        <i class="fas fa-music"></i> Song Parameters
      </button>
      <button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#agentTimeline" aria-expanded="true" aria-controls="agentTimeline">
        <i class="fas fa-stream"></i> Music Creation Timeline
      </button>
      <button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#agentConversations" aria-expanded="true" aria-controls="agentConversations">
        <i class="fas fa-comments"></i> Agent Conversations
      </button>
      <button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#musicAgentLogs" aria-expanded="true" aria-controls="musicAgentLogs">
        <i class="fas fa-file-alt"></i> Music Agent Logs
      </button>
      <button class="btn btn-primary" data-bs-toggle="collapse" data-bs-target="#sonicPiCode" aria-expanded="true" aria-controls="sonicPiCode">
        <i class="fas fa-code"></i> Sonic Pi Code
      </button>
    </div>

    <div class="row">
      <div id="songParameters" class="collapse show"><SongParameters   ref="songParametersRef" /></div>
      <div id="agentTimeline" class="collapse show"><AgentTimeline /></div>
      <AgentConversations  ref="agentConversationsRef" />
      <MusicAgentLogs  ref="sonicPiCodeRef" />
      <SonicPiCode />
    </div>
  </div>
  <footer class="container footer_container bg-dark text-white text-center py-3  mb-4">
    <div>
      <p class="mb-0">&copy; 2024 MusicAgent from mITyJohn. All rights reserved.</p>
      <p class="mb-0">Follow mITy.John on
        <a href="https://www.instagram.com/mity.john/" class="text-white"><i class="fab fa-instagram"></i></a>&nbsp;
        <a href="https://www.linkedin.com/in/jan-van-wassenhove-9b49893/" class="text-white"><i class="fab fa-linkedin"></i></a>&nbsp;
        <a href="https://mityjohn.com/" class="text-white"><i class="fab fa-wordpress"></i></a>&nbsp;
        <a href="https://x.com/mity_john" class="text-white"><i class="fab fa-twitter"></i></a>&nbsp;
      </p>
    </div>
  </footer>

</template>
<script>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import SongConfiguration from '@/components/SongConfiguration.vue'
import AgentTimeline from '@/components/AgentTimeline.vue'
import MusicAgentLogs from '@/components/MusicAgentLogs.vue'
import SonicPiCode from '@/components/SonicPiCode.vue'
import SongParameters from '@/components/SongParameters.vue'
import AgentConversations from '@/components/AgentConversations.vue'

export default {
  name: 'HomePage',
  components: {
    SongConfiguration,
    AgentTimeline,
    MusicAgentLogs,
    SonicPiCode,
    SongParameters,
    AgentConversations
  },
  setup() {
    const store = useStore()
    const formData = ref(store.state.formData)
    const logMessages = ref(store.state.logMessages)
    const songParameters = ref(store.state.songParameters)
    const currentPhase = ref(store.state.currentPhase)
    const completedPhases = ref(store.state.completedPhases)
    const formSubmitted = ref(false)
    const inputPrompt = ref('')
    const inputModal = ref(null)
    const eventSource = ref(null)
    const sonicPiCodeRef = ref(null)
    const agentConversationsRef = ref(null)

    const resetCurrentPhase = () => {
      currentPhase.value = ''
      completedPhases.value = []
    }

    const startEventSource = () => {
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
        if (formSubmitted.value && e.data.includes('"sonicpi_code"')) {
          if (formData.value.song_name && formData.value.song_name.trim() !== '') {
            sonicPiCodeRef.value.fetchSonicPiCode(formData.value.song_name);
          }
        }
        if (e.data === "DONE") {
          const completionAlert = document.getElementById('completionAlert')
          completionAlert.style.display = 'block'
          formSubmitted.value = false
          if (formData.value.song_name && formData.value.song_name.trim() !== '') {
            sonicPiCodeRef.value.fetchSonicPiCode(formData.value.song_name);
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
            console.log("Received message pushing to logMessages: " +e.data);
            logMessages.value.push(e.data);
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
      startEventSource()
    })

    return {
      formData,
      logMessages,
      currentPhase,
      completedPhases,
      formSubmitted,
      inputPrompt,
      inputModal,
      startEventSource,
      sonicPiCodeRef,
      agentConversationsRef

    }
  }
}

</script>