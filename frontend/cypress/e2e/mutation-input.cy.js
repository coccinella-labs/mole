// The mutation count the user typed must reach the API as a number, and an
// invalid entry must be refused in the browser with an explanation rather than
// turned into a request the API answers with an opaque 422.
//
// The specific defect: onChange did parseInt(e.target.value). Clearing the field
// makes that NaN, JSON.stringify writes NaN as null, and the API replies 422
// with a list-shaped detail that describeError could not render, so the person
// saw only "request failed with status 422".

const SMILES = 'CC(=O)OC1=CC=CC=C1C(=O)O'

const visitForm = () => {
  cy.visit('/')
  cy.get('input[type="text"]').type(SMILES)
}

const mutations = () => cy.get('input[type="number"]')
const generate = () => cy.get('button').contains('Generate Molecule')

describe('values the API accepts are sent through', () => {
  beforeEach(visitForm)

  it('sends 0 and shows the unchanged-structure notice', () => {
    cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body: {
      original_smiles: SMILES,
      generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
      molecular_image:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      properties: { 'Molecular Weight': 180.16, LogP: 1.31 },
      requested_mutations: 0, successful_mutations: 0, failed_mutations: 0, mutated: false,
    }}).as('gen')
    mutations().clear().type('0')
    generate().click()
    cy.wait('@gen').its('request.body.num_mutations').should('eq', 0)
    cy.contains('No mutation could be applied').should('be.visible')
  })

  it('sends 10, the upper bound, as a number not a string', () => {
    cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body: {
      original_smiles: SMILES,
      generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
      molecular_image:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      properties: { 'Molecular Weight': 180.16 },
      requested_mutations: 10, successful_mutations: 10, failed_mutations: 0, mutated: true,
    }}).as('gen')
    mutations().clear().type('10')
    generate().click()
    cy.wait('@gen').its('request.body.num_mutations').should('eq', 10)
  })

  it('sends 3, the default, without the field being touched', () => {
    cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body: {
      original_smiles: SMILES,
      generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
      molecular_image:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      properties: {},
      requested_mutations: 3, successful_mutations: 3, failed_mutations: 0, mutated: true,
    }}).as('gen')
    generate().click()
    cy.wait('@gen').its('request.body.num_mutations').should('eq', 3)
  })
})

describe('an emptied field is refused in the browser, not by the API', () => {
  beforeEach(visitForm)

  it('makes no request when the field is empty', () => {
    cy.intercept('POST', '**/generate_molecule').as('gen')
    mutations().clear()
    generate().click()
    cy.get('@gen.all').should('have.length', 0)
  })

  it('shows an explanation naming the accepted range', () => {
    cy.intercept('POST', '**/generate_molecule').as('gen')
    mutations().clear()
    generate().click()
    cy.contains('whole number between 0 and 10').should('be.visible')
    cy.get('@gen.all').should('have.length', 0)
  })

  it('shows inline guidance while the value is invalid, before any click', () => {
    mutations().clear()
    cy.contains('Enter a whole number between 0 and 10').should('be.visible')
  })

  it('removes the inline guidance once a valid value is typed', () => {
    mutations().clear()
    cy.contains('Enter a whole number between 0 and 10').should('be.visible')
    mutations().type('4')
    cy.contains('Enter a whole number between 0 and 10').should('not.exist')
  })

  it('treats a deliberate 0 differently from an empty field', () => {
    // The reason the state is a string: parseInt(value) || 0 would make an empty
    // field indistinguishable from a chosen 0, and 0 is a valid request.
    cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body: {
      original_smiles: SMILES,
      generated_smiles: SMILES,
      molecular_image:
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
      properties: {},
      requested_mutations: 0, successful_mutations: 0, failed_mutations: 0, mutated: false,
    }}).as('gen')
    mutations().clear()
    cy.contains('Enter a whole number between 0 and 10').should('be.visible')
    mutations().type('0')
    cy.contains('Enter a whole number between 0 and 10').should('not.exist')
    generate().click()
    cy.wait('@gen').its('request.body.num_mutations').should('eq', 0)
  })
})

describe('values outside the API range are refused in the browser', () => {
  beforeEach(visitForm)

  it('refuses 11 without a request', () => {
    cy.intercept('POST', '**/generate_molecule').as('gen')
    mutations().clear().type('11')
    generate().click()
    cy.get('@gen.all').should('have.length', 0)
    cy.contains('whole number between 0 and 10').should('be.visible')
  })

  it('refuses a negative value without a request', () => {
    cy.intercept('POST', '**/generate_molecule').as('gen')
    mutations().clear().type('-1')
    generate().click()
    cy.get('@gen.all').should('have.length', 0)
  })

  it('refuses a fractional value, since the API field is an int', () => {
    cy.intercept('POST', '**/generate_molecule').as('gen')
    mutations().clear().type('2.5')
    generate().click()
    cy.get('@gen.all').should('have.length', 0)
  })
})

describe('a 422 from the API is still readable if one arrives', () => {
  // describeError now handles FastAPI's list-shaped detail. This is the
  // defence-in-depth path: any schema violation reaching the browser should
  // name itself rather than degrade to a bare status code.
  it('shows the validation message rather than the status code', () => {
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', {
      statusCode: 422,
      body: {
        detail: [
          { type: 'int_type', loc: ['body', 'num_mutations'], msg: 'Input should be a valid integer' },
        ],
      },
    }).as('gen')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@gen')
    cy.contains('Input should be a valid integer').should('be.visible')
    cy.contains('status 422').should('not.exist')
  })
})

describe('the server explanation is not replaced by a generic client message', () => {
  it('still shows the full 400 detail for a count the client let through', () => {
    cy.visit('/')
    cy.get('input[type="text"]').type(SMILES)
    cy.intercept('POST', '**/generate_molecule', {
      statusCode: 400,
      body: {
        detail:
          'num_mutations must not exceed 10; each mutation searches up to 32 candidate positions, so the per-request cost grows with the requested count',
      },
    }).as('gen')
    cy.get('button').contains('Generate Molecule').click()
    cy.wait('@gen')
    cy.contains('must not exceed 10').should('be.visible')
    cy.contains('32 candidate positions').should('be.visible')
  })
})
