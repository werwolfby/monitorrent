import Vue from 'vue'
import DynamicFrom from 'src/components/DynamicForm'

describe('mtDynamicForm', () => {
    it('should render one row and 2 text inputs with default gutter (24) and username value', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {form: {rows, model: { username: 'monitorrent' }}}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-24')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.password).to.be.ok

        expect(vm.$refs.username.$el.className).to.contain('50')
        expect(vm.$refs.password.$el.className).to.contain('50')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('.md-input').value).to.be.equal('monitorrent')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')

        expect(vm.$refs.password.$el.querySelector('.md-input').type).to.be.equal('password')
        expect(vm.$refs.password.$el.querySelector('label').textContent).to.be.equal('Password')
    })

    it('should render 2 rows with text and select in 1st row and password and number in 2nd and gutter = 16', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 60
                }, {
                    type: 'select',
                    model: 'quality',
                    label: 'Quality',
                    flex: 40,
                    options: ['1080', '720', 'SD']
                }]
            },
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'host',
                    label: 'Host',
                    flex: 70
                }, {
                    type: 'number',
                    model: 'port',
                    label: 'Port',
                    flex: 30
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {form: {rows, model: { username: 'monitorrent' }}, gutter: 16}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row1).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-16')
        expect(vm.$refs.row1.$el.className).to.contain('md-gutter-16')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.quality).to.be.ok
        expect(vm.$refs.host).to.be.ok
        expect(vm.$refs.port).to.be.ok

        expect(vm.$refs.username.$el.className).to.contain('60')
        expect(vm.$refs.quality.$el.className).to.contain('40')
        expect(vm.$refs.host.$el.className).to.contain('70')
        expect(vm.$refs.port.$el.className).to.contain('30')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')

        expect(vm.$refs.quality.$el.querySelector('.md-select')).to.be.ok
        const qualityOptions = vm.$refs.quality.$el.querySelectorAll('.md-option')
        expect(qualityOptions).to.have.lengthOf(3)
        expect(qualityOptions[0].textContent).to.contain('1080')
        expect(qualityOptions[1].textContent).to.contain('720')
        expect(qualityOptions[2].textContent).to.contain('SD')

        expect(vm.$refs.host.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.host.$el.querySelector('label').textContent).to.be.equal('Host')

        expect(vm.$refs.port.$el.querySelector('.md-input').type).to.be.equal('number')
        expect(vm.$refs.port.$el.querySelector('label').textContent).to.be.equal('Port')
    })

    it('should ignore unknown input and render one row with 1 text input and default gutter (24)', () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'unknown',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {form: { rows }}}).$mount()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.row0.$el.className).to.contain('md-gutter-24')
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.password).to.be.not.ok

        expect(vm.$refs.username.$el.className).to.contain('50')

        expect(vm.$refs.username.$el.querySelector('.md-input').type).to.be.equal('text')
        expect(vm.$refs.username.$el.querySelector('label').textContent).to.be.equal('Username')
    })

    it('should update model on input change', async () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'text',
                    model: 'username',
                    label: 'Username',
                    flex: 50
                }, {
                    type: 'password',
                    model: 'password',
                    label: 'Password',
                    flex: 50
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {form: {rows, model: {username: 'monitorrent'}}}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.username).to.be.ok
        expect(vm.$refs.password).to.be.ok
        expect(vm.model.username).to.be.equal('monitorrent')
        expect(vm.model.password).to.be.null

        const usernameInput = vm.$refs['input-username']

        usernameInput.$el.value = 'username'
        usernameInput.onInput()

        const passwordInput = vm.$refs['input-password']

        passwordInput.$el.value = 'password'
        passwordInput.onInput()

        await Vue.nextTick()

        expect(vm.model.username).to.be.equal('username')
        expect(vm.model.password).to.be.equal('password')
    })

    it('should update model on select change', async () => {
        const rows = [
            {
                type: 'row',
                content: [{
                    type: 'select',
                    model: 'quality',
                    label: 'Quality',
                    flex: 100,
                    options: ['1080', '720', 'SD']
                }]
            }
        ]

        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor({propsData: {form: {rows, model: {quality: '720'}}}}).$mount()

        await Vue.nextTick()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.quality).to.be.ok
        expect(vm.model.quality).to.be.equal('720')

        const qualityInput = vm.$refs['input-quality']
        qualityInput.setTextAndValue('1080')
        qualityInput.changeValue('1080')

        await Vue.nextTick()

        expect(vm.model.quality).to.be.equal('1080')
    })

    it('should update model on each change rows', async () => {
        const Constructor = Vue.extend(DynamicFrom)
        const vm = new Constructor().$mount()

        await Vue.nextTick()

        expect(vm.$refs.row0).to.be.not.ok
        expect(vm.$refs.quality).to.be.not.ok

        vm.form = {
            rows: [
                {
                    type: 'row',
                    content: [{
                        type: 'select',
                        model: 'quality',
                        label: 'Quality',
                        flex: 100,
                        options: ['1080', '720', 'SD']
                    }]
                }
            ],
            model: {
                quality: '720'
            }
        }

        await Vue.nextTick()

        expect(vm.$refs.row0).to.be.ok
        expect(vm.$refs.quality).to.be.ok
        expect(vm.model).to.be.eql({quality: '720'})

        vm.form = {
            rows: [
                {
                    type: 'row',
                    content: [{
                        type: 'text',
                        model: 'username',
                        label: 'Username',
                        flex: 50
                    }, {
                        type: 'password',
                        model: 'password',
                        label: 'Password',
                        flex: 50
                    }]
                }
            ],
            model: {
                username: 'monitorrent'
            }
        }

        await Vue.nextTick()

        expect(vm.model).to.be.eql({username: 'monitorrent', password: null})
    })
})
