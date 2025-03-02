import { createRouter, createWebHistory } from 'vue-router';
import Welcome from '../views/Welcome.vue';
import Song from '../views/Song.vue';
import SampleList from '../views/SampleList.vue';
import SongsLibrary from '../views/SongsLibrary.vue';
import Settings from '../views/Settings.vue';

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome
  },
  {
    path: '/home',
    name: 'Song',
    component: Song
  },
  {
    path: '/samples',
    name: 'SampleList',
    component: SampleList
  },
  {
    path: '/songs-library',
    name: 'SongsLibrary',
    component: SongsLibrary
  },
  {
    path: '/settings', // Add the new route for Settings
    name: 'Settings',
    component: Settings
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
