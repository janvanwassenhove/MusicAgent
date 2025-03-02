<template>
  <div id="songParameters" class="collapse show">
    <h3>Song Input Parameters</h3>
    <div id="parameters" class="border p-3 mb-3">
      <div v-if="Object.keys(parameters).length === 0">No parameters received yet.</div>
      <div v-else>
        <div v-for="(value, key) in parameters" :key="key" class="mb-2 d-flex align-items-center">
          <strong>{{ key || 'undefined key' }}:</strong>
          <span :class="{ 'collapsed-text': !expandedKeys[key], 'expanded-text': expandedKeys[key] }" class="ml-2">
            {{ value || 'undefined value' }}
          </span>
          <button v-if="value && value.length > 50" @click="toggleExpand(key)" class="ml-2 btn btn-link p-0">
            <i :class="expandedKeys[key] ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'SongParameters',
  data() {
    return {
      expandedKeys: {}
    }
  },
  computed: {
    ...mapState({
      parameters: state => state.songParameters
    })
  },
  methods: {
    toggleExpand(key) {
      this.expandedKeys = { ...this.expandedKeys, [key]: !this.expandedKeys[key] };
    }
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
.collapsed-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 200px; /* Adjust as needed */
}

.expanded-text {
  white-space: normal;
}

button.btn-link {
  border: none;
  color: inherit;
  text-decoration: none;
}
.d-flex {
  display: flex;
  align-items: center;
}

.ml-2 {
  margin-left: 0.5rem; /* Adjust as needed */
}
</style>