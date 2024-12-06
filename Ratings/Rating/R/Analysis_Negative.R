


# Last inn nødvendig bibliotek
library(jsonlite)
library(dplyr)
library(ggplot2)
library(lubridate)
library(tidyr)

# Les JSON-filen
# Erstatt 'path/to/your/file.json' med den faktiske filbanen til din JSON-fil
data <- fromJSON('Processed_Google_ratings_2.json', simplifyVector = TRUE)

# Konverter data til en tibble (dataframe)
data <- as_tibble(data)

# Vis de første radene i datasettet
head(data)

# Vis strukturen til datasettet
str(data)

# Hvis 'categories' er en liste-kolonne, kan du konvertere den til separate kolonner
data <- data %>%
  mutate(across(where(is.list), as.data.frame),
         Dato = ymd(substr(Dato, 1, 10))) %>% 
  unnest_wider(categories) %>% 
  rename(
    Positiv = `Positiv tilbakemelding`,
    Dyre_P = `Dyre produkter`,
    Produkter = `Dårlige produkter`,
    Kundeservice = `Dårlig kundeservice/opplevelse`,
    Ventetid = `Lang kø/ventetid`,
    Renhold = `Dårlig renhold`,
    Kommentar = `Ingen kommentar`,
    Annet_N = `Annet Dårlig`,
    Rating= `★`
  ) %>% 
  filter(Dato > '2019-12-31',
         Dato < '2025-01-01',
         Avd != "16 EV") 

nrow(data)

colnames(data)



# Test_2 ------------------------------------------------------------------

# Funksjon for å lage gyldig formel med forklaringsgrad
generate_valid_formula <- function(department_data) {
  # Bygg lineær modell
  model <- lm(Rating ~ Positiv + Dyre_P + Produkter + Kundeservice + Ventetid + Renhold + Annet_N,
              data = department_data)
  
  # Hent modellresultater og filtrer kun signifikante variabler
  coefficients <- broom::tidy(model) %>%
    filter(p.value < 0.05) %>%
    select(term, estimate)
  
  # Beregn forklaringsgrad (R^2)
  model_summary <- summary(model)
  r_squared <- model_summary$r.squared
  
  # Hvis ingen signifikante variabler finnes, returner konstantledd med R^2
  if (nrow(coefficients) == 0) {
    intercept <- mean(department_data$Rating, na.rm = TRUE)
    return(list(
      Formel = paste0("Rating = ", sprintf("%.3f", intercept)),
      Forklaringsgrad = sprintf("%.3f", r_squared)
    ))
  }
  
  # Hent konstantleddet (Intercept)
  intercept <- coefficients %>% filter(term == "(Intercept)") %>% pull(estimate)
  
  # Hvis konstantleddet mangler, bruk gjennomsnittet som konstantledd
  if (length(intercept) == 0) {
    intercept <- mean(department_data$Rating, na.rm = TRUE)
  }
  
  # Legg til signifikante prediktorer
  predictors <- coefficients %>%
    filter(term != "(Intercept)") %>%
    mutate(term = gsub("`", "", term)) %>%
    mutate(formula_segment = paste0(sprintf("%.3f", estimate), term)) %>%
    pull(formula_segment)
  
  # Lag formelstrengen
  formula_string <- paste0("Rating = ", sprintf("%.3f", intercept))
  if (length(predictors) > 0) {
    formula_string <- paste0(formula_string, " + ", paste(predictors, collapse = " + "))
  }
  
  return(list(Formel = formula_string, Forklaringsgrad = sprintf("%.3f", r_squared)))
}

# Generer formler og forklaringsgrad for hver avdeling
formulas <- data %>%
  group_by(Avd) %>%
  group_map(~ generate_valid_formula(.x), .keep = TRUE) %>%
  setNames(unique(data$Avd))

# Lag en dataframe med forklaringsgrad og formler
formulas_df <- tibble(
  Avdeling = names(formulas),
  Formel = sapply(formulas, function(x) x$Formel),
  Forklaringsgrad = sapply(formulas, function(x) x$Forklaringsgrad)
)

# Fjern NA-resultater (ugyldige modeller)
formulas_df <- formulas_df %>%
  filter(!is.na(Formel))

# Vis formler med forklaringsgrad
print(formulas_df, n = Inf)

# Lagre resultatene i en CSV-fil
write.csv(formulas_df, "validerte_formler_med_forklaringsgrad.csv", row.names = FALSE)


# Test 2 ------------------------------------------------------------------




# Last inn nødvendig bibliotek
library(jsonlite)
library(dplyr)
library(ggplot2)
library(lubridate)
library(tidyr)

# Les JSON-filen
# Erstatt 'path/to/your/file.json' med den faktiske filbanen til din JSON-fil
data <- fromJSON('Processed_Google_ratings_2.json', simplifyVector = TRUE)

# Konverter data til en tibble (dataframe)
data <- as_tibble(data)

# Vis de første radene i datasettet
head(data)

# Vis strukturen til datasettet
str(data)

# Hvis 'categories' er en liste-kolonne, kan du konvertere den til separate kolonner
data <- data %>%
  mutate(across(where(is.list), as.data.frame),
         Dato = ymd(substr(Dato, 1, 10))) %>% 
        unnest_wider(categories) %>% 
  rename(
    Positiv = `Positiv tilbakemelding`,
    Dyre_P = `Dyre produkter`,
    Produkter = `Dårlige produkter`,
    Kundeservice = `Dårlig kundeservice/opplevelse`,
    Ventetid = `Lang kø/ventetid`,
    Renhold = `Dårlig renhold`,
    Kommentar = `Ingen kommentar`,
    Annet_N = `Annet Dårlig`,
    Rating= `★`
  ) %>% 
  filter(Dato > '2010-12-31',
         Dato < '2025-01-01',
         Avd != "16 EV") 

nrow(data)

colnames(data)


# Regresjon ---------------------------------------------------------------

# Funksjon for å utføre regresjon per avdeling
run_regression <- function(department_data) {
  # Kontroller datastruktur
  if (!"Rating" %in% colnames(department_data)) {
    stop("Kolonnen 'Rating' finnes ikke i department_data")
  }
  
  # Bygg lineær modell
  model <- lm(Rating ~ Positiv + Dyre_P +  Produkter + Kundeservice + Ventetid + Renhold + Kommentar + Annet_N,
              data = department_data)
  
  # Hent resultater og filtrer basert på p-verdi
  tidy(model) %>%
    mutate(Significant = p.value < 0.05) %>%
    arrange(term) %>%
    select(term, estimate, p.value, Significant)
}

# Bruk regresjonsfunksjonen for hver avdeling
regression_results <- data %>%
  group_by(Avd) %>%
  group_map(~ run_regression(.x), .keep = TRUE) %>%
  setNames(unique(data$Avd))

# Kombiner resultatene i en matrise og sortér etter avdeling
final_results <- do.call(rbind, lapply(names(regression_results), function(name) {
  cbind(Avdeling = name, regression_results[[name]])
}))

# Konverter til data frame
final_results <- as.data.frame(final_results)

# Sorter resultatene etter avdeling
final_results <- final_results[order(final_results$Avdeling), ]

# Vis resultatene
print(final_results)



# Kul å forklare intercept ------------------------------------------------


# Filtrer kun signifikante resultater
all_effects <- final_results %>%
  filter(Significant == TRUE, 
         term != "Kommentar"
  ) %>%
  mutate(estimate_abs = abs(as.numeric(estimate)))

# Visualisering Regresjon kul for å forklare  --------------------------------

# Filtrer kun signifikante resultater
significant_effects <- final_results %>%
  filter(Significant == TRUE, 
         term != "(Intercept)",
         term != "Kommentar",
         term != "Positiv"
         ) %>%
  mutate(estimate_abs = abs(as.numeric(estimate)))

# Lag et heatmap
ggplot(significant_effects, aes(x = term, y = Avdeling, fill = estimate_abs)) +
  geom_tile(color = "white") +
  scale_fill_gradient(low = "blue", high = "red", name = "Absolutt effekt") +
  labs(
    title = "Signifikante variabler per avdeling",
    x = "Variabel",
    y = "Avdeling"
  ) +
  theme_minimal() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1, size = 10),
    axis.text.y = element_text(size = 10),
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
    legend.position = "right",
    legend.title = element_text(size = 12),
    legend.text = element_text(size = 10)
  )

