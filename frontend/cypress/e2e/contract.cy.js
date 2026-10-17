// These tests assert that the counters in the API response reach the user as
// the numbers shown on screen. Each case uses a different set of values on
// purpose: if the UI rendered a hardcoded default, the differing numbers would
// fail here instead of passing silently.

const payload = (over) => ({
  original_smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O',
  generated_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
  molecular_image:
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  properties: { 'Molecular Weight': 180.16, LogP: 1.31 },
  ...over,
})

const submit = (body) => {
  cy.intercept('POST', '**/generate_molecule', { statusCode: 200, body }).as('gen')
  cy.visit('/')
  cy.get('input[placeholder*="SMILES"]').type('CC(=O)OC1=CC=CC=C1C(=O)O')
  cy.get('button').contains('Generate Molecule').click()
  cy.wait('@gen')
}

describe('mutation counter display (response contract)', () => {
  it('shows every requested mutation applied and reports no rejections', () => {
    submit(payload({ requested_mutations: 3, successful_mutations: 3, failed_mutations: 0, mutated: true }))
    cy.contains('Mutations Applied').should('be.visible')
    cy.contains('3 of 3 applied').should('be.visible')
    cy.contains('rejected:').should('not.exist')
    cy.contains('No mutation could be applied').should('not.exist')
  })

  it('shows the applied count and the rejected count', () => {
    submit(payload({ requested_mutations: 7, successful_mutations: 5, failed_mutations: 2, mutated: true }))
    cy.contains('5 of 7 applied').should('be.visible')
    cy.contains('2 rejected: no valid change could be made').should('be.visible')
    cy.contains('No mutation could be applied').should('not.exist')
  })

  it('shows the zero-success notice when nothing was mutated', () => {
    submit(payload({ requested_mutations: 4, successful_mutations: 0, failed_mutations: 4, mutated: false }))
    cy.contains('0 of 4 applied').should('be.visible')
    cy.contains('4 rejected: no valid change could be made').should('be.visible')
    cy.contains('No mutation could be applied').should('be.visible')
    cy.contains('unchanged from the input').should('be.visible')
  })

  it('shows a single applied mutation out of many', () => {
    submit(payload({ requested_mutations: 12, successful_mutations: 1, failed_mutations: 11, mutated: true }))
    cy.contains('1 of 12 applied').should('be.visible')
    cy.contains('11 rejected: no valid change could be made').should('be.visible')
  })
})
