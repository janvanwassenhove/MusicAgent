<template>
  <div class="row mt-4">
    <div class="col-12 py-4">
      <form @submit.prevent="submitForm">
        <h3>Song Configuration</h3>
        <!-- Form content -->
      </form>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'SongConfiguration',
  computed: {
    ...mapState(['formData', 'genres', 'agentTypes'])
  },
  methods: {
    ...mapActions(['submitForm', 'initializeAgent'])
  }
}
</script>
