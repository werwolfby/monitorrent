<template>
  <md-card class="topics-list">
    <md-card-content>
      <md-list class="md-double-line" disabled="True">
        <md-list-item>
          <md-avatar>
            <img src="static/images/rutor.info.png"/>
          </md-avatar>

          <div class="md-list-text-container">
            <span>Теория Большого Взрыва / The Big Bang Theory S10</span>
            <span>Last update: 06.02.2017 20:54:24</span>
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
  name: 'topics'
}
</script>

<style>
.topics-list {
  margin: 16px
}
</style>
