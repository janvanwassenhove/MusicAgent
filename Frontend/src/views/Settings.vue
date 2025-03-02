<!-- Filename: Settings.vue -->
<template>
  <MainLayout>
    <h1>Music Agent Settings</h1>
    <p>Configure your Music Agent settings here.</p>
    <ul class="nav nav-tabs" id="settingsTabs" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link active" id="general-tab" data-bs-toggle="tab" data-bs-target="#general" type="button" role="tab" aria-controls="general" aria-selected="true">General</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="sonicpi-tab" data-bs-toggle="tab" data-bs-target="#sonicpi" type="button" role="tab" aria-controls="sonicpi" aria-selected="false">Sonic Pi Configuration</button>
      </li>
    </ul>
    <div class="tab-content" id="settingsTabsContent">
      <div class="tab-pane fade show active" id="general" role="tabpanel" aria-labelledby="general-tab">
        <p>
          Artist Styling
        </p>
      </div>
      <div class="tab-pane fade" id="sonicpi" role="tabpanel" aria-labelledby="sonicpi-tab">
        <h4>Sonic Pi Configuration</h4>
        <p>Local IP</p>
        <p>Incoming OSC Port</p>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import MainLayout from "@/layouts/MainLayout.vue";

export default {
  name: 'AgentSettings' ,
  components: {MainLayout}
}
</script>

<style scoped>

/* Add any specific styles for the settings view here */
.nav-tabs {
  border-bottom: 1px solid #1A4731
}

.nav-tabs .nav-item {
  margin-bottom: -1px;
}

.nav-tabs .nav-link {
  border: 1px solid transparent ;
  border-top-left-radius: 0.25rem;
  border-top-right-radius: 0.25rem;
  color: #FFA500;
  font-weight: bold;
}

.nav-tabs .nav-link:hover {
  border-color: #e9ecef #e9ecef #ddd;
}

.nav-tabs .nav-link.active {
  color: #111;
  background-color: #fff;
  border-color: #1A4731 #1A4731 #fff;
}

.tab-content {
  border: 1px solid #1A4731;
  border-top: none;
  padding: 1rem;
  background-color: #fff;
}

</style>