describe('Mole e2e', () => {
  it('loads the app and displays the title', () => {
    cy.visit('/')
    cy.contains('Mole').should('be.visible')
  })

  it('generates a molecule', () => {
    cy.visit('/')
    cy.get('input[placeholder*="SMILES"]').type('CC(=O)OC1=CC=CC=C1C(=O)O')
    cy.get('input[type="number"]').clear().type('1')
    cy.get('button').contains('Generate Molecule').click()
    cy.contains('Generated Molecule').should('be.visible')
    cy.get('img').should('be.visible')
  })
})
