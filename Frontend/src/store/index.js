import { createStore } from 'vuex'
import axios from 'axios'

export default createStore({
    state: {
        formData: {
            genre: '',
            duration: 180,
            additional_information: '',
            song_name: '',
            agent_type: 'mITyJohn',
            api_provider: 'openai',
            selected_model: 'gpt-4o-mini'
        },
        formSubmitted: false,
        agentInitialized: false,
        errors: {},
        genres: [],
        agentTypes: [],
        availableModels: [],
        timeline: [],
        currentPhase: '',
        completedPhases: [],
        currentCycle: {},
        songParameters: {},
        logMessages: [],
        sonicPiCodeVersions: [],
        selectedProvider: localStorage.getItem('selectedProvider') || 'openai',
        selectedModel: localStorage.getItem('selectedModel') || '',
        providers: [],
        modelsByProvider: {}
    },
    mutations: {
        addSonicPiCodeVersion(state, newCode) {
            state.sonicPiCodeVersions.push(newCode);
        },
        setFormSubmitted(state, value) {
            state.formSubmitted = value;
        },
        setTimeline(state, timeline) {
            state.timeline = timeline;
        },
        setErrors(state, errors) {
            state.errors = errors
        },
        setFormData(state, data) {
            state.formData = { ...state.formData, ...data }
            console.log("Updated formData:", state.formData);
        },
        setAgentInitialized(state, value) {
            state.agentInitialized = value
        },
        setGenres(state, genres) {
            state.genres = genres
        },
        setAgentTypes(state, types) {
            state.agentTypes = types
        },
        setAvailableModels(state, availableModels) {
            state.availableModels = availableModels
        },
        setCurrentPhase(state, phase) {
            state.currentPhase = phase;
        },
        addCompletedPhase(state, phase) {
            if (!state.completedPhases.includes(phase)) {
                state.completedPhases.push(phase);
            }
        },
        setProviders(state, providers) {
            state.providers = providers
        },
        setModelsByProvider(state, { provider, models }) {
            state.modelsByProvider = {
                ...state.modelsByProvider,
                [provider]: models
            }
        },
        setSelectedProvider(state, provider) {
            state.selectedProvider = provider
            localStorage.setItem('selectedProvider', provider)
        },
        setSelectedModel(state, model) {
            state.selectedModel = model
            localStorage.setItem('selectedModel', model)
        },
    },
    actions: {
        async fetchAgentTypes({ commit }) {
            try {
                const response = await fetch('/agent_types')
                const data = await response.json()
                commit('setAgentTypes', data.agent_types)
            } catch (error) {
                console.error('Error fetching agent types:', error)
            }
        },
        async fetchModelConfig({ commit }) {
            try {
                const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/model_config`)
                const data = response.data
                commit('setProviders', Object.keys(data))
            } catch (error) {
                console.error('Error fetching model config:', error)
            }
        },
        async updateModelOptions({ commit }, provider) {
            try {
                const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/model_config/${provider}`)
                commit('setModelsByProvider', { provider, models: Object.keys(response.data) })
            } catch (error) {
                console.error('Error fetching models:', error)
            }
        }
    },
    getters: {
        availableModels: state => state.modelsByProvider[state.selectedProvider] || []
    }
})
