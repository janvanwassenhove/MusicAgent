<template>
  <MainLayout>
    <div class="container">
      <h1 class="my-4">Samples</h1>
      <button class="btn btn-primary" @click="runSampleMetadataListing">Run Sample Metadata Listing</button>
      <div v-if="isRunning" class="progress mt-3">
        <div class="progress-bar" role="progressbar" :style="{ width: progress + '%' }" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">{{ progress }}%</div>
      </div>
      <hr>
      <div class="input-group mb-3">
        <input type="text" class="form-control" placeholder="Search samples..." v-model="searchQuery" @input="filterSamples">
      </div>
      <ul class="list-group mt-4">
        <li v-for="sample in paginatedSamples" :key="sample.Filename" class="list-group-item">
          <div class="d-flex justify-content-between align-items-center">
            <span @click="toggleDetails(sample.Filename)" style="cursor: pointer;">{{ sample.Filename }}</span>
            <button class="btn btn-secondary btn-sm" @click="playSample(sample.Filename)">Play</button>
          </div>
          <div v-if="visibleSample === sample.Filename" class="mt-2">
            <p><strong>Duration:</strong> {{ sample.Duration }}
            <br><strong>BPM:</strong> {{ sample.BPM }}
            <br><strong>Key:</strong> {{ sample.Key }}
            <br><strong>Vibe:</strong> {{ sample.Vibe }}
            <br><strong>Tags:</strong> {{ sample.Tags.join(', ') }}
            <br><strong>Description:</strong> {{ sample.Description }}</p>
          </div>
        </li>
      </ul>
      <div v-if="filteredSamples.length > samplesPerPage" class="d-flex justify-content-center mt-3">
        <button class="btn btn-primary" @click="prevPage" :disabled="currentPage === 1">Previous</button>
        <span class="mx-2 mt-2">Page {{ currentPage }} of {{ totalPages }}</span>
        <span class="mx-2 mt-2">Total Samples: {{ filteredSamples.length }}</span>
        <button class="btn btn-primary" @click="nextPage" :disabled="currentPage === totalPages">Next</button>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import axios from 'axios';
import MainLayout from '@/layouts/MainLayout.vue';

export default {
  name: 'SampleList',
  components: {
    MainLayout
  },
  data() {
    return {
      isRunning: false,
      progress: 0,
      samples: [],
      filteredSamples: [],
      currentPage: 1,
      samplesPerPage: 10,
      visibleSample: null,
      searchQuery: ''
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.filteredSamples.length / this.samplesPerPage);
    },
    paginatedSamples() {
      const start = (this.currentPage - 1) * this.samplesPerPage;
      const end = start + this.samplesPerPage;
      return this.filteredSamples.slice(start, end);
    }
  },
  methods: {
    async runSampleMetadataListing() {
      this.isRunning = true;
      this.progress = 0;
      try {
        await axios.post(`${process.env.VUE_APP_API_URL}/api/run_sample_metadata_listing`);
        this.checkProgress();
      } catch (error) {
        console.error('Error starting sample metadata listing:', error);
        this.isRunning = false;
      }
    },
    async checkProgress() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample_metadata_progress`);
        this.progress = parseFloat(response.data.progress.toFixed(2));
        if (this.progress < 100 && this.progress >= 0) {
          setTimeout(this.checkProgress, 1000);
        } else {
          this.isRunning = false;
        }
      } catch (error) {
        console.error('Error checking progress:', error);
        this.isRunning = false;
      }
    },
    async fetchSamples() {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample_metadata`);
        this.samples = response.data;
        this.filteredSamples = this.samples;
      } catch (error) {
        console.error('Error fetching samples:', error);
      }
    },
    filterSamples() {
      const query = this.searchQuery.toLowerCase();
      this.filteredSamples = this.samples.filter(sample => sample.Filename.toLowerCase().includes(query));
      this.currentPage = 1; // Reset to the first page after filtering
    },
    async playSample(filename) {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample/${filename}`, { responseType: 'blob' });
        const url = URL.createObjectURL(response.data);
        const audio = new Audio(url);
        audio.play();
      } catch (error) {
        console.error('Error playing sample:', error);
      }
    },
    toggleDetails(filename) {
      this.visibleSample = this.visibleSample === filename ? null : filename;
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    }
  },
  mounted() {
    this.fetchSamples();
  }
};
</script>

<style scoped>
.progress {
  height: 30px;
}

.progress-bar {
  line-height: 30px;
}
</style>