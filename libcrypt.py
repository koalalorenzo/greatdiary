#!/usr/bin/env python
# -*- coding=utf-8 -*-

#Libreria per criptare/decriptare una stringa in base ad una chiave.
def crypt(valore,chiave):
    """Riceve la stringa valore da cifrare e la chiave.
    
    Si ricava il numero S dato dalla somma dei valori ASCII di ogni
    carattere di chiave più 42. La stringa restituita è formattata
    in una serie di sequenze del tipo "#x#" dove x è il valore ASCII
    di un carattere di valore sommato ad S. Il numero di tali sequenze,
    ovviamente, è pari a quello dei caratteri della stringa di partenza."""
    chiave = str(chiave)
    valore = str(valore)
    somma_chiave = 0
    for lettera in chiave:
        somma_chiave = somma_chiave + ord(lettera)
    somma_chiave = somma_chiave + 42
    risultato = ""
    for lettera in valore:
        somma_lettera = ord(lettera) + somma_chiave
        risultato = "%s#%s#" % (risultato, somma_lettera)
    return risultato
    
def decrypt(valore,chiave):
    """Riceve la stringa cifrata valore e la chiave.
    
    Si ricava il numero S dato dalla somma dei valori ASCII di ogni
    carattere di chiave più 42. Si ricavano gli interi x da ogni sequenza
    "#x#" di valore e ad esso si sottrae S. I caratteri corrispondenti
    ad ogni x vengono concatenati per restituire la stringa in chiaro."""
    chiave = str(chiave)
    valore = str(valore)
    somma_chiave = 0
    for lettera in chiave:
        somma_chiave = somma_chiave + ord(lettera)
    somma_chiave = somma_chiave + 42
    risultato = ""
    listvalore = valore.split("#")
    for lettera in listvalore:
        if not lettera == '':
            numero = int(lettera) - somma_chiave
            risultato = "%s%s" % (risultato,chr(numero))
    return risultato
