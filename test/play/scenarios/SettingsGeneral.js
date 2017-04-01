import { play } from 'vue-play'
import SettingsGeneral from '../../../src/components/Settings/SettingsGeneral'

play(SettingsGeneral)
    .add('empty', h => <md-whiteframe md-elevation="5" style="margin: auto; width: 1168px"><SettingsGeneral></SettingsGeneral></md-whiteframe>)
