<template>
  <MainLayout>
    <img src="@/assets/images/road_robots.png" alt="Road Robots" class="responsive-image" />
    <br/><br>
    <h1>Welcome to MusicAgent</h1>

    <p>🎵 Welcome to Music Agent!
Ready to bring your musical ideas to life? You’re in the right place.<br/>

👉 Start a new track by clicking "New Song" in the navigation bar.<br/>
🎧 Explore and play with inspiration via the "Samples" section — perfect for discovering example songs or checking your newly added samples.<br/>
📚 Dive into your creations in the "Songs Library", where all your saved songs live.<br/>
⚙️ Want to fine-tune your setup? Visit "Settings" to configure Sonic Pi, tweak styles, and personalize your experience.<br/>
<br/>
Let the jam begin!
</p>
  </MainLayout>
</template>

<script>
import MainLayout from '@/layouts/MainLayout.vue'

export default {
  name: 'WelcomePage',
  components: {
    MainLayout
  }
}
</script>

<style scoped>
.responsive-image {
  max-width: 100%;
  height: auto;
}
</style>
