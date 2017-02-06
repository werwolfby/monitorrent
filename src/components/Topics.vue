<template>
  <md-card class="topics-list">
    <md-card-content>
      <md-list class="md-double-line" disabled="True">
        <md-list-item v-for="topic in topics">
          <md-avatar>
            <img v-bind:src="'static/images/' + topic.tracker + '.png'"/>
          </md-avatar>

          <div class="md-list-text-container">
            <span>{{topic.display_name}}</span>
            <span>Last update: {{topic.last_update}}</span>
          </div>

          <md-menu class="md-secondary" md-direction="bottom left" md-size="4">
            <md-button md-menu-trigger class="md-icon-button">
              <md-icon>more_vert</md-icon>
            </md-button>
            <md-menu-content md-size="4">
              <md-menu-item>
                <md-icon>edit</md-icon> Edit
              </md-menu-item>
              <md-menu-item>
                <md-icon>pause</md-icon> Pause
              </md-menu-item>
              <md-menu-item>
                <md-icon>restore</md-icon> Reset Status
              </md-menu-item>
              <md-menu-item>
                <md-icon>input</md-icon> Execute
              </md-menu-item>
            </md-menu-content>
          </md-menu>
        </md-list-item>
      </md-list>
    </md-card-content>
  </md-card>
</template>

<script>
export default {
  data: () => {
    return {
      'topics': []
    }
  },
  name: 'topics',
  mounted () {
    fetch('/api/topics')
    .then(data => data.json())
    .then(data => {
      console.log(data)
      this.topics = data
    })
  }
}
</script>

<style>
.topics-list {
  margin: 16px
}
</style>
