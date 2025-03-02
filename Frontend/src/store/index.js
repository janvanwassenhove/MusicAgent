import { createStore } from 'vuex'

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
        sonicPiCodeVersions: []
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
    },
    actions: {
        updateModelOptions({ commit, state }) {
            const modelOptions = {
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4-32k"],
                "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
            }
            const availableModels = modelOptions[state.formData.api_provider] || []
            commit('setAvailableModels', availableModels)
            if (!availableModels.includes(state.formData.selected_model)) {
                state.formData.selected_model = availableModels[0] || ''
            }
        },
        async fetchAgentTypes({ commit }) {
            try {
                const response = await fetch('/agent_types')
                const data = await response.json()
                commit('setAgentTypes', data.agent_types)
            } catch (error) {
                console.error('Error fetching agent types:', error)
            }
        }
    }
})
