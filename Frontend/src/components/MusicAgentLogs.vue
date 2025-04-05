<template>
  <div id="musicAgentLogs" class="py-4 collapse show">
    <h3>Music Agent Logs</h3>
    <div id="log" class="mt-4 cli-log py-4">
      <pre><code><span v-for="(message, index) in logMessages" :key="index" v-text="message"></span></code></pre>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'MusicAgentLogs',
  computed: {
    ...mapState({
      logMessages: state => state.logMessages
    })
  }
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>
