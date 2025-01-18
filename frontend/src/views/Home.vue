<template>
  <div class="text-center py-2 mb-2" style="background-color: #1A4731;">
    <img src="/static/musicagent.png" alt="MusicAgent" style="max-width: 100%; height: 200px;">
  </div>

  <div class="container main_container p-4">
    <SongConfiguration />
    <hr>
    <div class="row">
      <Timeline />
      <AgentConversations />
      <MusicAgentLogs />
      <SonicPiCode />
    </div>
  </div>

  <!-- Modals -->
  <input-modal />
  <config-modal />
  <error-modal />
</template>

<script>
import SongConfiguration from '@/components/SongConfiguration.vue'
import Timeline from '@/components/Timeline.vue'
import AgentConversations from '@/components/AgentConversations.vue'
import MusicAgentLogs from '@/components/MusicAgentLogs.vue'
import SonicPiCode from '@/components/SonicPiCode.vue'

export default {
  name: 'HomePage',
  components: {
    SongConfiguration,
    Timeline,
    AgentConversations,
    MusicAgentLogs,
    SonicPiCode
  }
}
</script>

