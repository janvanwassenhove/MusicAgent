<template>
  <div class="row mt-4">
    <div class="col-12 py-4">
      <form @submit.prevent="submitForm" v-if="formData">
        <h1>Song Configuration</h1>
        <div class="row">
          <div class="col-md-4 mb-3">
            <label for="api_provider" class="form-label">API Provider:</label>
            <select v-model="formData.api_provider" id="api_provider" class="form-select" @change="updateModelOptions" required>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
          <div class="col-md-4 mb-3">
            <label for="selected_model" class="form-label">Model:</label>
            <select v-model="formData.selected_model" id="selected_model" class="form-select" required>
              <option v-for="model in availableModels" :key="model" :value="model" v-text="model"></option>
            </select>
          </div>
          <div class="col-md-4 mb-3">
            <label for="agent_type" class="form-label">Select Agent Type:</label>
            <div class="input-group">
              <select v-model="formData.agentType" id="agent_type" class="form-select" @change="initializeAgent">
                <option v-for="type in agentTypes" :key="type" :value="type" v-text="type"></option>
              </select>
              <button class="btn btn-outline-secondary" @click="openConfigDialog" :disabled="!formData.agentType">
                <i class="fas fa-cog"></i>
              </button>
            </div>
          </div>
          <div v-if="formData.api_provider === 'anthropic'" class="col-12 mb-3">
            <div class="alert alert-warning" role="alert">
              <i class="fas fa-exclamation-triangle me-2"></i>
              Warning: Cover art creation won't be possible due to model restrictions when using Anthropic.
            </div>
          </div>
        </div>
        <div class="row" v-if="agentInitialized">
          <div class="col-md-6 mb-3">
            <label  class="form-label">Song Name:</label>
            <input v-model="formData.song_name" type="text" id="song_name" class="form-control" :class="{'is-invalid': errors.song_name}" required>
            <div class="invalid-feedback" v-if="errors.song_name" v-text="errors.song_name"></div>
          </div>
          <div class="col-md-3 mb-3">
            <label for="genre" class="form-label">Genre:</label>
            <select v-model="formData.genre" id="genre" class="form-select" :class="{'is-invalid': errors.genre}" required>
              <option v-for="genre in genres" :key="genre" :value="genre.genre" v-text="genre.genre"></option>
            </select>
            <div class="invalid-feedback" v-if="errors.genre" v-text="errors.genre"></div>
          </div>
          <div class="col-md-3 mb-3">
            <label for="duration" class="form-label">Duration [seconds]:</label>
            <input v-model.number="formData.duration" type="number" id="duration" class="form-control" :class="{'is-invalid': errors.duration}" required value="180">
            <div class="invalid-feedback" v-if="errors.duration" v-text="errors.duration"></div>
          </div>
          <div class="col-md-9 mb-3">
            <label for="additional_information" class="form-label">How do you imagine your song?</label>
            <textarea rows="4" v-model="formData.additional_information" id="additional_information" class="form-control" :class="{'is-invalid': errors.additional_information}" placeholder="The track opens with a rich, atmospheric intro, blending soft ambient pads with subtle rhythmic clicks that evolve into a groovy, energetic beat. The song transitions into a dynamic arrangement, combining uplifting melodies with deep basslines, creating a captivating interplay of light and intensity. The middle section introduces a vocal chop or melodic hook that becomes the centerpiece of the track. The bridge brings a stripped-back moment, offering a reflective pause before a climactic, high-energy finale. The overall mood is empowering and celebratory, perfect for a vibrant dance floor or a driving anthem."></textarea>
            <div class="invalid-feedback" v-if="errors.additional_information" v-text="errors.additional_information"></div>
          </div>
          <div class="col-md-3 mb-3 justify-content-end d-flex align-items-end">
            <button type="submit" class="btn btn-primary">Generate Music</button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div class="modal fade" id="configModal" tabindex="-1" aria-labelledby="configModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="configModalLabel">Edit {{ formData.agentType }} Configuration</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <textarea id="configJson" v-model="configJson" class="form-control json-textarea" rows="20" style="max-height: 60vh; overflow-y: auto;"></textarea>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-primary" @click="saveConfig">Save changes</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import axios from 'axios'
import * as bootstrap from 'bootstrap'

export default {
  name: 'SongConfiguration',
  data() {
    return {
      configJson: ''
    }
  },
  computed: {
    ...mapState({
      formData: state => state.formData,
      genres: state => state.genres,
      agentTypes: state => state.agentTypes,
      availableModels: state => state.availableModels,
      agentInitialized: state => state.agentInitialized,
      errors: state => state.errors
    })
  },
  methods: {
    ...mapActions(['submitForm', 'initializeAgent', 'updateModelOptions', 'openConfigDialog']),
    async fetchAgentTypes() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/agent_types`)
        if (response.data && response.data.agent_types) {
          this.$store.commit('setAgentTypes', response.data.agent_types)
        } else {
          console.error('Unexpected response format:', response.data)
        }
      } catch (error) {
        console.error('Error fetching agent types:', error)
      }
    },
    async initializeAgent() {
      if (!this.formData.agentType) return
      console.log("Before API call - formData:", this.formData)
      try {
        const response = await axios.post(`${process.env.VUE_APP_API_URL}/api/init`, { agent_type: this.formData.agentType })

        console.log("After API call - formData:", this.formData)
        if (response.data && response.data.genres) {
          this.$store.commit('setGenres', response.data.genres)
          this.$store.commit('setAgentInitialized', true)
        } else {
          console.error('Unexpected response format:', response.data)
        }
      } catch (error) {
        console.error('Error initializing agent:', error)
      }
    },
    async openConfigDialog() {
      if (!this.formData.agentType) return

      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/agent_config/${this.formData.agentType}`)
        this.configJson = JSON.stringify(response.data, null, 2)
        this.$nextTick(() => {
          if (!this.configModal) {
            this.configModal = new bootstrap.Modal(document.getElementById('configModal'))
          }
          this.configModal.show()
        })
      } catch (error) {
        console.error('Error fetching agent config:', error)
      }
    },
    async saveConfig() {
      try {
        const parsedConfig = JSON.parse(this.configJson)
        const response = await axios.post(`${process.env.VUE_APP_API_URL}/api/agent_config/${this.formData.agentType}`, parsedConfig)
        if (response.data.message === "Configuration saved successfully") {
          if (!this.configModal) {
            this.configModal = new bootstrap.Modal(document.getElementById('configModal'))
          }
          this.configModal.hide()
          await this.initializeAgent()
        } else {
          console.error('Unexpected response format:', response.data)
        }
      } catch (error) {
        console.error('Error saving agent config:', error)
        alert('Invalid JSON or error saving configuration')
      }
    },
    validateForm() {
      this.errors = {}
      if (!this.formData.genre) {
        this.errors.genre = 'Please select a genre'
      }
      if (!this.formData.duration || this.formData.duration <= 0) {
        this.errors.duration = 'Please enter a valid duration'
      }
      if (!this.formData.song_name.trim()) {
        this.errors.song_name = 'Please enter a song name'
      }
      return Object.keys(this.errors).length === 0
    },
    submitForm() {
      if (this.validateForm()) {
        this.$store.commit('setFormSubmitted', true)
        axios.post(`${process.env.VUE_APP_API_URL}/api/create`, this.formData)
            .then(() => {
              this.$emit('formSubmitted')
            })
            .catch(error => {
              console.error('Error submitting form:', error)
            })
      } else {
        console.log('Form validation failed')
      }
    },
  },
  mounted() {
    console.log("FormData:", this.formData);
    this.fetchAgentTypes();
    this.updateModelOptions();
    if (this.agentTypes.length > 0) {
      this.formData.agentType = this.agentTypes[0]; // Set the first agent type by default
      this.initializeAgent();
    }
  }
}
</script>
