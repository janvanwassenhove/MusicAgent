<template>
  <div id="timeline" class="col-md-6 py-4">
    <h3>Music Creation Timeline</h3>
    <ul class="list-group" v-if="agentInitialized">
      <li v-for="(phase, index) in timeline" :key="index" class="list-group-item"
          :class="{
          'bg-info text-white': phase.phase === currentPhase,
          'bg-success text-white': completedPhases.includes(phase.phase),
          'bg-light': !completedPhases.includes(phase.phase) && phase.phase !== currentPhase
          }">
        <div class="d-flex justify-content-between align-items-center">
          <span>
            <span class="badge bg-primary rounded-pill me-2">{{ index + 1 }}</span>
            {{ phase.phase }}
          </span>
          <span v-if="phase.phaseType === 'ComposedPhase'" class="badge rounded-pill">
            Cycles: {{ cycleCount(phase) }}/{{ phase.cycleNum }}
          </span>
          <span v-else-if="isSubphaseOfComposed(phase)" class="badge bg-secondary rounded-pill">
            Parent Cycles: {{ cycleCount(phase) }}
          </span>
        </div>
        <ul v-if="phase.phaseType === 'ComposedPhase'" class="list-group mt-2">
          <li v-for="(subphase, subindex) in phase.Composition" :key="subindex"
              class="list-group-item list-group-item-secondary"
              :class="{
              'bg-info text-white': subphase.phase === currentPhase,
              'bg-success text-white': completedPhases.includes(subphase.phase),
              'bg-light': !completedPhases.includes(subphase.phase) && subphase.phase !== currentPhase
              }">
            <span class="badge bg-secondary rounded-pill me-2">{{ index + 1 }}.{{ subindex + 1 }}</span>
            {{ subphase.phase }}
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'AgentTimeline',
  computed: {
    ...mapState({
      timeline: state => state.timeline,
      currentPhase: state => state.currentPhase,
      completedPhases: state => state.completedPhases,
      currentCycle: state => state.currentCycle
    })
  },
  methods: {
    cycleCount() {
      return (phase) => {
        if (phase.phaseType === 'ComposedPhase') {
          const count = phase.phase in this.currentCycle ? this.currentCycle[phase.phase].count : 0;
          return count;
        } else {
          // For SimplePhase, find the parent ComposedPhase
          const parentComposedPhase = this.timeline.find(p =>
              p.phaseType === 'ComposedPhase' &&
              p.Composition.some(subphase => subphase.phase === phase.phase)
          );
          if (parentComposedPhase) {
            const count = parentComposedPhase.phase in this.currentCycle ? this.currentCycle[parentComposedPhase.phase].count : 0;
            return count;
          }
          return 0;
        }
      }
    },
    isSubphaseOfComposed() {
      return (phase) => {
        return this.timeline.some(p =>
            p.phaseType === 'ComposedPhase' &&
            p.Composition.some(subphase => subphase.phase === phase.phase)
        );
      }
    }
  }
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>