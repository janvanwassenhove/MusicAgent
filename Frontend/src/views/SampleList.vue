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
      <hr>
      <div class="input-group mb-3">
        <input type="text" class="form-control" placeholder="Search samples..." v-model="searchQuery" @input="filterSamples">
      </div>
      <ul class="list-group mt-4">
        <li v-for="sample in paginatedSamples" :key="sample.Filename" class="list-group-item">
          <div class="d-flex justify-content-between align-items-center">
            <span @click="toggleDetails(sample.Filename)" style="cursor: pointer;">{{ sample.Filename }}</span>
          </div>
          <div v-if="visibleSample === sample.Filename" class="mt-2">
            <div class="row">
              <div class="col-md-9">
                <p><strong>Duration:</strong> {{ sample.Duration }}
                  <br><strong>BPM:</strong> {{ sample.BPM }}
                  <br><strong>Key:</strong> {{ sample.Key }}
                  <br><strong>Vibe:</strong> {{ sample.Vibe }}
                  <br><strong>Tags:</strong> {{ sample.Tags.join(', ') }}
                  <br><strong>Description:</strong> {{ sample.Description }}</p>
              </div>
              <div class="col-md-3 player">
                <canvas :id="`canvas-${sample.Filename}`" class="spectrum-canvas"></canvas>
                <div class="player-controls">
                  <button class="btn btn-secondary btn-sm" @click="togglePlayPause(sample.Filename)">
                    <i :class="isPlaying && currentSample === sample.Filename ? 'fas fa-pause' : 'fas fa-play'"></i>
                  </button>&nbsp;
                  <button class="btn btn-secondary btn-sm" @click="stopSample(sample.Filename)">
                    <i class="fas fa-stop"></i>
                  </button>&nbsp;
                  <span class="player-time"><b>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</b></span>
                </div>
              </div>
            </div>
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
      isPlaying: false,
      audioContext: null,
      analyser: null,
      dataArray: null,
      currentTime: 0,
      duration: 0
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
          url: URL.createObjectURL(new Blob([sample.data], {type: 'audio/mpeg'}))
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
        const response = await axios.get(`${process.env.VUE_APP_API_URL}/api/sample/${filename}`, {responseType: 'blob'});
        const url = URL.createObjectURL(response.data);
        this.audio = new Audio(url);
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        const source = this.audioContext.createMediaElementSource(this.audio);
        source.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);

        this.audio.onloadedmetadata = () => {
          this.duration = this.audio.duration;
        };

        this.audio.play();
        this.currentSample = filename;
        this.isPlaying = true;

        this.audio.ontimeupdate = () => {
          this.currentTime = this.audio.currentTime;
        };

        this.visualize(filename);
      } catch (error) {
        console.error('Error playing sample:', error);
      }
    },
    visualize(filename) {
      const canvas = document.getElementById(`canvas-${filename}`);
      const canvasContext = canvas.getContext('2d');
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;

      const draw = () => {
        requestAnimationFrame(draw);
        if (!this.audio) return; // Add this check to ensure this.audio is not null
        this.analyser.getByteFrequencyData(this.dataArray);
        canvasContext.fillStyle = '#1A4731';
        canvasContext.fillRect(0, 0, canvas.width, canvas.height);

        // Draw the frequency bars
        const barWidth = (canvas.width / this.dataArray.length) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < this.dataArray.length; i++) {
          barHeight = this.dataArray[i] / 2; // Adjust the bar height calculation
          canvasContext.fillStyle = '#FFA500';
          canvasContext.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
          x += barWidth + 1;
        }

        // Draw the current playback position line
        const currentTime = this.audio.currentTime;
        const duration = this.audio.duration;
        const lineX = (currentTime / duration) * canvas.width;

        canvasContext.strokeStyle = 'white';
        canvasContext.beginPath();
        canvasContext.moveTo(lineX, 0);
        canvasContext.lineTo(lineX, canvas.height);
        canvasContext.stroke();
      };
      draw();
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
        this.audio.ontimeupdate = null; // Remove the event listener
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
      if (this.visibleSample === filename) {
        this.visibleSample = null;
        this.currentTime = 0;
        this.duration = 0;
      } else {
        this.visibleSample = filename;
        this.currentTime = 0; // Reset currentTime
        this.duration = 0; // Reset duration
      }
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
    },
    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
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

.spectrum-canvas {
  width: 100%;
  height: 75%;
  background-color: #1A4731;
  border-radius: 8px;
  margin-bottom: 5px
}

.player {
  border: 1px solid;
  padding: 3px;
  border-radius: 12px;
  background-color: #212429;
}

.player-controls {
  display: inline;
  padding-left: 5px;
}

.player-time {
  color: #FFA500; 
  text-align: right; 
  margin-left: 15px;
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
