<template>
  <div id="timeline">
    <h3>Music Creation Timeline</h3>
    <ul class="list-group" v-if="agentInitialized">
      <li v-for="(phase, index) in timeline.filter(p => p && p.phaseType)" :key="index" class="list-group-item"
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
        <ul v-if="phase && phase.phaseType === 'ComposedPhase'" class="list-group mt-2">
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
import axios from 'axios'

export default {
  name: 'AgentTimeline',
  computed: {
    ...mapState({
      agentInitialized: state => state.agentInitialized,
      timeline: state => state.timeline || [],
      currentPhase: state => state.currentPhase,
      completedPhases: state => state.completedPhases,
      currentCycle: state => state.currentCycle,
      formData: state => state.formData
    })
  },
  methods: {
    cycleCount(phase) {
      if (!phase || !phase.phaseType) {
        console.warn('cycleCount received undefined phase', phase);
        return 0;
      }

      if (phase.phaseType === 'ComposedPhase') {
        return this.currentCycle?.[phase.phase]?.count || 0;
      }

      const parentComposedPhase = this.timeline?.find(p =>
          p.phaseType === 'ComposedPhase' &&
          p.Composition?.some(subphase => subphase.phase === phase.phase)
      );

      if (parentComposedPhase) {
        return this.currentCycle?.[parentComposedPhase.phase]?.count || 0;
      }

      return 0;
    },
    isSubphaseOfComposed() {
      return (phase) => {
        if (!phase || !phase.phaseType) {
          return false;
        }

        return (this.timeline || []).some(p =>
            p.phaseType === 'ComposedPhase' &&
            (p.Composition || []).some(subphase => subphase.phase === phase.phase)
        );
      };
    },
    async fetchTimeline() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/timeline`, {
          params: { agent_type: this.formData.agentType }
        });
        this.$store.commit('setTimeline', response.data.chain);

      } catch (error) {
        console.error('Error fetching timeline:', error);
      }
    },
    processPhaseStart(data) {
      const phaseStartMatch = data.match(/Executing phase: \[(.+)\]/);
      if (phaseStartMatch) {
        const newPhase = phaseStartMatch[1].trim();

        // Find the parent ComposedPhase
        const composedPhase = this.timeline.find(phase =>
            phase.phaseType === 'ComposedPhase' &&
            phase.Composition.some(subphase => subphase.phase === newPhase)
        );

        if (composedPhase) {
          const composedPhaseName = composedPhase.phase;
          if (!(composedPhaseName in this.currentCycle)) {
            console.log("Initializing currentCycle for", composedPhaseName);
            this.$store.state.currentCycle[composedPhaseName] = {
              count: 0,
              currentSubphase: ''
            };
          }

          // Check if we're starting the first subphase
          if (composedPhase.Composition[0].phase === newPhase &&
              this.currentCycle[composedPhaseName].currentSubphase !== newPhase) {
            this.currentCycle[composedPhaseName].count++;
          }
          this.$store.state.currentCycle[composedPhaseName].currentSubphase = newPhase;

          // Check if all cycles are finished
          if (this.currentCycle[composedPhaseName].count === composedPhase.cycleNum) {
            this.$store.commit('addCompletedPhase', composedPhaseName);
          }
        }

        if (this.currentPhase) {
          this.$store.commit('addCompletedPhase', this.currentPhase);
        }
        this.$store.commit('setCurrentPhase', newPhase);
      }
    }
  },
  watch: {
    'formData.agentType': function() {
      this.fetchTimeline();
    },
    timeline(newVal) {
      console.log('Timeline updated:', newVal);
    }
  },
  mounted() {
    this.fetchTimeline();
  }
}
</script>

<style scoped>
/* Add any component-specific styles here */
</style>