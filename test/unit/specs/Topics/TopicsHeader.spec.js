import Vue from 'vue'
import TopicsHeader from 'src/components/Topics/TopicsHeader'

describe('TopicsHeader.vue', () => {
  const Constructor = Vue.extend(TopicsHeader)

  it('should render correct content', () => {
    const vm = new Constructor().$mount()
    expect(vm.$el.querySelector('#filter')).to.not.be.null
    expect(vm.$el.querySelector('#order')).to.not.be.null
    expect(vm.$el.querySelector('#add')).to.not.be.null
  })

  it('should have empty values by default', () => {
    const vm = new Constructor().$mount()
    expect(vm.$el.querySelector('#filter')).to.have.property('value').equal('')
    expect(vm.$el.querySelector('#order')).to.have.property('value').equal('')
  })

  it('should have values equal to props', async () => {
    const props = { filter: 'lostfilm.tv', order: '-last_update' }
    const vm = new Constructor({ propsData: props }).$mount()

    await Vue.nextTick()

    expect(vm.$el.querySelector('#filter')).to.have.property('value').equal('lostfilm.tv')
    expect(vm.$el.querySelector('#order')).to.have.property('value').equal('-last_update')
  })
})
