<template>
  <div id="songParameters" class="col-md-6 py-4 collapse show">
    <h3>Song Input Parameters</h3>
    <div id="parameters" class="border p-3 mb-3">
      <div v-if="Object.keys(parameters).length === 0">No parameters received yet.</div>
      <div v-else>
        <div v-for="(value, key) in parameters" :key="key" class="mb-2">
          <strong>{{ key || 'undefined key' }}:</strong> {{ value || 'undefined value' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'SongParameters',
  computed: {
    ...mapState({
      parameters: state => state.songParameters
    })
  },
  watch: {
    parameters(newVal) {
      console.info('Updated parameters:', newVal);
    }
  },
  mounted() {
    console.info('Initial parameters:', this.parameters);
  }
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>