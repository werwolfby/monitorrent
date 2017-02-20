<template>
  <div id="app">
    <md-toolbar>
      <h2 class="md-title">
        Monitorrent
        <span class="md-title-caption">v.1.1.2a</span>
      </h2>
      <span style="flex: 1"></span>
      <md-button class="md-icon-button">
        <md-icon>settings</md-icon>
      </md-button>
      <md-button class="md-icon-button">
        <md-icon>exit_to_app</md-icon>
      </md-button>
    </md-toolbar>

    <div class="mt-content-view">
      <md-whiteframe md-elevation="5">
        <router-view></router-view>
      </md-whiteframe>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'
import VueMaterial from 'vue-material'
import { formatDate, isNull } from './filters'

Vue.use(VueMaterial)

Vue.material.registerTheme('default', {
    primary: 'blue-grey',
    accent: 'deep-purple',
    warn: 'deep-orange',
    background: 'white'
})

Vue.filter('formatDate', formatDate)
Vue.filter('isNull', isNull)

export default {
    name: 'app'
}
</script>

<style>
.md-title-caption {
  font-size: 12px;
  letter-spacing: 0.020em;
}

.mt-content-view {
  margin: auto;
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
  padding: 16px;
}
</style>
