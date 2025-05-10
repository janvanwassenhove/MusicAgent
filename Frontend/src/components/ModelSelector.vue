<template>
  <div class="col-md-8 mb-3">
    <div class="row">
      <div class="col-md-6">
        <label for="api_provider" class="form-label">Provider:</label>
        <select v-model="selectedProvider" id="api_provider" class="form-select" @change="handleProviderChange">
          <option v-for="provider in providers" :key="provider" :value="provider">
            {{ provider.charAt(0).toUpperCase() + provider.slice(1) }}
          </option>
        </select>
      </div>
      <div class="col-md-6">
        <label for="selected_model" class="form-label">Model:</label>
        <select v-model="selectedModel" id="selected_model" class="form-select" @change="handleModelChange">
          <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ModelSelector',
  data() {
    return {
      providers: [],
      selectedProvider: this.$store.state.formData.api_provider,
      selectedModel: this.$store.state.formData.selected_model
    }
  },
  computed: {
    availableModels() {
      return this.$store.state.modelsByProvider[this.selectedProvider] || []
    }
  },
  methods: {
    async fetchModelConfig() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/model_config`)
        this.providers = Object.keys(response.data)
        if (this.providers.length > 0) {
          // Set default provider if none selected
          if (!this.selectedProvider) {
            this.selectedProvider = this.providers[0]
          }

          // Get models for selected provider
          const modelResponse = await axios.get(`${process.env.VUE_APP_API_URL}/api/model_config/${this.selectedProvider}`)
          const models = Object.keys(modelResponse.data)

          // Set models in store
          this.$store.commit('setModelsByProvider', {
            provider: this.selectedProvider,
            models: models
          })

          // Initialize selected model if not already set
          if (!this.selectedModel && models.length > 0) {
            this.selectedModel = models[0]
            this.$store.commit('setFormData', {
              selected_model: this.selectedModel,
              api_provider: this.selectedProvider
            })
          }
        }
      } catch (error) {
        console.error('Error fetching model config:', error)
      }
    },
    async handleProviderChange() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/model_config/${this.selectedProvider}`)
        this.$store.commit('setModelsByProvider', {
          provider: this.selectedProvider,
          models: Object.keys(response.data)
        })

        // Update form data with new provider
        this.$store.commit('setFormData', {
          api_provider: this.selectedProvider
        })

        // Set first available model if current one is not available
        if (this.availableModels.length > 0 && !this.availableModels.includes(this.selectedModel)) {
          this.selectedModel = this.availableModels[0]
          this.handleModelChange()
        }
      } catch (error) {
        console.error('Error fetching models:', error)
      }
    },
    handleModelChange() {
      this.$store.commit('setFormData', {
        selected_model: this.selectedModel
      })
    }
  },
  async mounted() {
    await this.fetchModelConfig()
  },
  watch: {
    '$store.state.formData.api_provider'(newValue) {
      if (newValue !== this.selectedProvider) {
        this.selectedProvider = newValue
      }
    },
    '$store.state.formData.selected_model'(newValue) {
      if (newValue !== this.selectedModel) {
        this.selectedModel = newValue
      }
    }
  }
}
</script>