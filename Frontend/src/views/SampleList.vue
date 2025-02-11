<template>
  <MainLayout>
    <div class="container">
      <h1 class="my-4">Samples</h1>
      <span>Run sample metadata listing after uploading new samples so they'll be enlisted during song creation.</span><br/>
      <button class="btn btn-primary mt-2" @click="runSampleMetadataListing">Run Sample Metadata Listing</button>
      <div v-if="isRunning" class="progress mt-3">
        <div class="progress-bar" role="progressbar" :style="{ width: progress + '%' }" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">{{ progress }}%</div>
      </div>
      <hr>
      <span>Select your sample(s) you'd like to use in your songs:</span><br/>
      <div class="input-group mb-3 mt-3">
        <input type="file" class="form-control" @change="handleFileUpload" multiple>
        <button class="btn btn-primary" @click="uploadSamples">Upload Samples</button>
      </div>
      <hr><av-line :line-width="2" line-color="lime" src="/static/music.mp3"></av-line>
      <div class="input-group mb-3">
        <input type="text" class="form-control" placeholder="Search samples..." v-model="searchQuery" @input="filterSamples">
      </div>
      <ul class="list-group mt-4">
        <li v-for="sample in paginatedSamples" :key="sample.Filename" class="list-group-item">
          <div class="d-flex justify-content-between align-items-center">
            <span @click="toggleDetails(sample.Filename)" style="cursor: pointer;">{{ sample.Filename }}</span>
            <div>
              <button class="btn btn-secondary btn-sm" @click="togglePlayPause(sample.Filename)">
                <i :class="isPlaying && currentSample === sample.Filename ? 'fas fa-pause' : 'fas fa-play'"></i>
              </button>
              <button class="btn btn-secondary btn-sm" @click="stopSample(sample.Filename)">
                <i class="fas fa-stop"></i>
              </button>
            </div>
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
      searchQuery: '',
      files: [],
      audio: null,
      currentSample: null,
      isPlaying: false
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
        this.samples = response.data.map(sample => ({
          ...sample,
          url: URL.createObjectURL(new Blob([sample.data], { type: 'audio/mpeg' }))
        }));
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
      if (this.audio && this.currentSample === filename) {
        this.audio.play();
        this.isPlaying = true;
        return;
      }
      if (this.audio) {
        this.audio.pause();
      }
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample/${filename}`, { responseType: 'blob' });
        const url = URL.createObjectURL(response.data);
        this.audio = new Audio(url);
        this.audio.play();
        this.currentSample = filename;
        this.isPlaying = true;
      } catch (error) {
        console.error('Error playing sample:', error);
      }
    },
    pauseSample() {
      if (this.audio) {
        this.audio.pause();
        this.isPlaying = false;
      }
    },
    stopSample() {
      if (this.audio) {
        this.audio.pause();
        this.audio.currentTime = 0;
        this.audio = null;
        this.currentSample = null;
        this.isPlaying = false;
      }
    },
    togglePlayPause(filename) {
      if (this.isPlaying && this.currentSample === filename) {
        this.pauseSample();
      } else {
        this.playSample(filename);
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
    },
    handleFileUpload(event) {
      const files = event.target.files || event;
      this.files = [...this.files, ...files];
    },
    async uploadSamples() {
      const formData = new FormData();
      for (let i = 0; i < this.files.length; i++) {
        formData.append('files', this.files[i]);
      }
      try {
        await axios.post(`${process.env.VUE_APP_API_URL}/api/upload_samples`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        this.fetchSamples(); // Refresh the sample list after upload
      } catch (error) {
        console.error('Error uploading samples:', error);
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
  background-color: #1A4731;
  color: white;
  line-height: 30px;
}

.drop-zone {
  border: 2px dashed #ccc;
  padding: 20px;
  text-align: center;
  cursor: pointer;
}

.drop-zone.dragging {
  border-color: #1A4731;
  background-color: #f0f0f0;
}
</style>