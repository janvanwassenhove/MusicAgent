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
        genres: [],
        agentTypes: [],
        timeline: [],
        currentPhase: '',
        completedPhases: [],
        parameters: {},
        logMessages: []
    },
    mutations: {
        setFormData(state, data) {
            state.formData = { ...state.formData, ...data }
        },
        setGenres(state, genres) {
            state.genres = genres
        },
        setAgentTypes(state, types) {
            state.agentTypes = types
        }
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
        }
    }
})
