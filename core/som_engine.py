"""
StoryMap SOM — Núcleo de inteligencia artificial
Implementación de Self-Organizing Map (SOM) de Kohonen para análisis de textos.

Autores: Santiago Castañeda & Santiago Florez
Curso: Computación Blanda
"""

import numpy as np
import re
import json
import os
from collections import defaultdict


# ─── Preprocesamiento de texto ────────────────────────────────────────────────

STOPWORDS_ES = {
    "de","la","que","el","en","y","a","los","del","se","las","un","por",
    "con","no","una","su","para","es","al","lo","como","más","pero","sus",
    "le","ya","o","este","sí","porque","esta","entre","cuando","muy",
    "sin","sobre","también","me","hasta","hay","donde","quien","desde",
    "todo","nos","durante","todos","uno","les","ni","contra","otros","ese",
    "eso","ante","ellos","e","esto","mí","antes","algunos","qué","unos",
    "yo","otro","otras","él","tanto","esa","estos","mucho","quienes","nada",
    "muchos","cual","sea","poco","ella","estar","estas","algunas","algo",
    "nosotros","mi","mis","tú","te","ti","tu","tus","vosotros","vosotras",
    "os","mío","mía","míos","mías","tuyo","tuya","tuyos","tuyas","suyo",
    "the","is","in","it","of","and","to","a","that","was","he","for","on",
    "are","with","his","they","at","be","this","from","or","had","by","not",
    "have","but","what","all","were","we","when","your","can","said","there",
    "use","an","each","which","she","do","how","their","if","will","up","other",
    "about","out","many","then","them","these","so","some","her","would","make",
    "like","him","into","time","has","look","two","more","go","see","no","way",
    "could","people","my","than","first","been","call","who","its","now","did",
    "get","come","made","may","part","i","s","t","don","you"
}

STOPWORDS_EN = {
    "the","is","in","it","of","and","to","a","that","was","he","for","on",
    "are","with","his","they","at","be","this","from","or","had","by","not",
    "have","but","what","all","were","we","when","your","can","said","there"
}


def tokenize(text: str) -> list:
    """Limpia y tokeniza un texto eliminando stopwords."""
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñ\s]", " ", text)
    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 2 and t not in STOPWORDS_ES]
    return tokens


def build_vocabulary(documents: list) -> dict:
    """Construye vocabulario global de todos los documentos."""
    vocab = defaultdict(int)
    for doc in documents:
        for token in tokenize(doc):
            vocab[token] += 1
    # Filtrar palabras muy raras (< 2 apariciones)
    vocab = {w: i for i, (w, c) in enumerate(sorted(vocab.items())) if c >= 1}
    return vocab


def tfidf_vectors(documents: list, vocab: dict) -> np.ndarray:
    """
    Calcula vectores TF-IDF para cada documento.
    TF-IDF = Term Frequency × Inverse Document Frequency
    """
    N = len(documents)
    V = len(vocab)
    matrix = np.zeros((N, V))

    # TF
    tokenized = [tokenize(d) for d in documents]
    for i, tokens in enumerate(tokenized):
        for token in tokens:
            if token in vocab:
                matrix[i, vocab[token]] += 1
        if len(tokens) > 0:
            matrix[i] /= len(tokens)

    # IDF
    df = np.sum(matrix > 0, axis=0) + 1
    idf = np.log((N + 1) / df) + 1
    matrix *= idf

    # Normalización L2
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix /= norms

    return matrix


# ─── Self-Organizing Map (Kohonen) ────────────────────────────────────────────

class SOMKohonen:
    """
    Implementación de SOM de Kohonen para clustering de documentos de texto.

    El SOM aprende una proyección topológica de un espacio de alta dimensión
    (vectores TF-IDF) a una grilla 2D, preservando relaciones de similitud.

    Parámetros:
        grid_size (tuple): Dimensiones de la grilla (filas, columnas)
        n_features (int): Dimensión del vector de entrada
        learning_rate (float): Tasa de aprendizaje inicial η₀
        sigma (float): Radio inicial de vecindad σ₀
        max_iter (int): Número máximo de iteraciones
    """

    def __init__(self, grid_size=(8, 8), n_features=100,
                 learning_rate=0.5, sigma=None, max_iter=500):
        self.rows, self.cols = grid_size
        self.n_features = n_features
        self.lr0 = learning_rate
        self.sigma0 = sigma or max(self.rows, self.cols) / 2.0
        self.max_iter = max_iter
        self.iteration = 0
        self.quantization_errors = []

        # Pesos: cada neurona tiene un vector de pesos w ∈ ℝ^n_features
        self.weights = np.random.randn(self.rows, self.cols, n_features) * 0.1

        # Coordenadas de neuronas en la grilla
        self._coords = np.array([
            [r, c] for r in range(self.rows) for c in range(self.cols)
        ], dtype=float)

    def _learning_rate(self, t: int) -> float:
        """η(t) = η₀ · exp(−t / λ) — decaimiento exponencial."""
        λ = self.max_iter / np.log(self.lr0 + 1e-9 + 1)
        return self.lr0 * np.exp(-t / max(λ, 1))

    def _sigma(self, t: int) -> float:
        """σ(t) = σ₀ · exp(−t / λ_σ) — reducción del radio de vecindad."""
        λ_σ = self.max_iter / np.log(self.sigma0 + 1e-9 + 1)
        return self.sigma0 * np.exp(-t / max(λ_σ, 1))

    def _neighborhood(self, bmu_r: int, bmu_c: int, sigma: float) -> np.ndarray:
        """
        Función de vecindad gaussiana h(t) = exp(−d² / 2σ²)
        donde d es la distancia en la grilla al BMU.
        """
        bmu_coord = np.array([bmu_r, bmu_c], dtype=float)
        dists_sq = np.sum((self._coords - bmu_coord) ** 2, axis=1)
        h = np.exp(-dists_sq / (2 * sigma ** 2 + 1e-9))
        return h.reshape(self.rows, self.cols, 1)

    def find_bmu(self, x: np.ndarray):
        """Encuentra Best Matching Unit (neurona más cercana al vector x)."""
        diff = self.weights - x
        dists = np.linalg.norm(diff, axis=2)
        idx = np.unravel_index(np.argmin(dists), dists.shape)
        return idx, dists[idx]

    def train_step(self, x: np.ndarray, t: int):
        """Un paso de entrenamiento del SOM."""
        bmu_idx, dist = self.find_bmu(x)
        lr = self._learning_rate(t)
        sigma = self._sigma(t)
        h = self._neighborhood(bmu_idx[0], bmu_idx[1], sigma)
        # Δw = η(t) · h(t) · (x − w)
        self.weights += lr * h * (x - self.weights)
        return dist

    def train(self, X: np.ndarray, callback=None):
        """
        Entrena el SOM con los datos X.
        callback(progreso 0-100, qe): función opcional para reportar progreso.
        """
        self.quantization_errors = []
        n = len(X)
        for t in range(self.max_iter):
            # Selección aleatoria de muestra
            idx = np.random.randint(0, n)
            qe = self.train_step(X[idx], t)
            self.quantization_errors.append(qe)
            self.iteration = t + 1

            if callback and t % 20 == 0:
                progress = int((t / self.max_iter) * 100)
                avg_qe = np.mean(self.quantization_errors[-20:])
                callback(progress, avg_qe)

        if callback:
            callback(100, np.mean(self.quantization_errors[-10:]))

    def map_documents(self, X: np.ndarray) -> list:
        """Asigna cada documento a su BMU en la grilla."""
        positions = []
        for x in X:
            bmu, dist = self.find_bmu(x)
            positions.append({"row": int(bmu[0]), "col": int(bmu[1]), "dist": float(dist)})
        return positions

    def u_matrix(self) -> np.ndarray:
        """
        Calcula la U-Matrix: distancia media entre neuronas vecinas.
        Útil para visualizar fronteras entre clusters.
        """
        u = np.zeros((self.rows, self.cols))
        for r in range(self.rows):
            for c in range(self.cols):
                neighbors = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        neighbors.append(np.linalg.norm(
                            self.weights[r,c] - self.weights[nr,nc]
                        ))
                u[r,c] = np.mean(neighbors) if neighbors else 0
        return u

    def cluster_labels(self, positions: list, n_clusters: int = 5) -> list:
        """Asigna etiquetas de cluster usando K-Means sobre posiciones del SOM."""
        from sklearn.cluster import KMeans
        coords = np.array([[p["row"], p["col"]] for p in positions])
        if len(coords) < n_clusters:
            n_clusters = len(coords)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(coords)
        return labels.tolist()

    def top_words_per_cluster(self, labels: list, documents: list,
                               vocab: dict, n: int = 8) -> dict:
        """Retorna las palabras más representativas por cluster."""
        inv_vocab = {v: k for k, v in vocab.items()}
        clusters = defaultdict(list)
        for i, (doc, label) in enumerate(zip(documents, labels)):
            clusters[label].append(doc)

        result = {}
        for label, docs in clusters.items():
            word_freq = defaultdict(int)
            for doc in docs:
                for token in tokenize(doc):
                    word_freq[token] += 1
            top = sorted(word_freq.items(), key=lambda x: -x[1])[:n]
            result[label] = [w for w, _ in top]
        return result

    def get_state(self) -> dict:
        """Serializa el estado del SOM para guardar/cargar."""
        return {
            "rows": self.rows,
            "cols": self.cols,
            "n_features": self.n_features,
            "lr0": self.lr0,
            "sigma0": self.sigma0,
            "max_iter": self.max_iter,
            "iteration": self.iteration,
            "weights": self.weights.tolist(),
            "qe_history": self.quantization_errors[-100:],
        }

    @classmethod
    def from_state(cls, state: dict) -> "SOMKohonen":
        """Carga un SOM desde estado serializado."""
        som = cls(
            grid_size=(state["rows"], state["cols"]),
            n_features=state["n_features"],
            learning_rate=state["lr0"],
            sigma=state["sigma0"],
            max_iter=state["max_iter"],
        )
        som.weights = np.array(state["weights"])
        som.iteration = state["iteration"]
        som.quantization_errors = state.get("qe_history", [])
        return som


# ─── Gestor de sesión ─────────────────────────────────────────────────────────

class StorySession:
    """
    Gestiona una sesión de análisis: documentos, SOM, resultados.
    """

    def __init__(self):
        self.documents = []       # textos crudos
        self.titles = []          # títulos/nombres de archivo
        self.vocab = {}           # vocabulario
        self.vectors = None       # matriz TF-IDF
        self.som = None           # modelo SOM entrenado
        self.positions = []       # posición BMU de cada documento
        self.labels = []          # etiquetas de cluster
        self.top_words = {}       # palabras clave por cluster
        self.grid_size = (8, 8)
        self.n_clusters = 5
        self.max_iter = 300

    def add_document(self, title: str, text: str):
        """Agrega un documento a la sesión."""
        self.titles.append(title)
        self.documents.append(text)

    def remove_document(self, idx: int):
        """Elimina un documento por índice."""
        if 0 <= idx < len(self.documents):
            self.documents.pop(idx)
            self.titles.pop(idx)

    def clear(self):
        """Limpia todos los documentos y resultados."""
        self.__init__()

    def prepare(self):
        """Prepara vectores TF-IDF a partir de documentos cargados."""
        if len(self.documents) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para el análisis.")
        self.vocab = build_vocabulary(self.documents)
        if len(self.vocab) == 0:
            raise ValueError("No se pudo construir vocabulario. Verifica el contenido.")
        self.vectors = tfidf_vectors(self.documents, self.vocab)
        return len(self.vocab)

    def train(self, callback=None):
        """Entrena el SOM con los vectores preparados."""
        if self.vectors is None:
            raise RuntimeError("Llama prepare() antes de train().")
        n_feat = self.vectors.shape[1]
        self.som = SOMKohonen(
            grid_size=self.grid_size,
            n_features=n_feat,
            learning_rate=0.5,
            max_iter=self.max_iter,
        )
        self.som.train(self.vectors, callback=callback)
        self.positions = self.som.map_documents(self.vectors)
        self.labels = self.som.cluster_labels(self.positions, self.n_clusters)
        self.top_words = self.som.top_words_per_cluster(
            self.labels, self.documents, self.vocab
        )
        return self.positions

    def get_map_data(self) -> dict:
        """Retorna todos los datos necesarios para visualizar el mapa."""
        if not self.positions:
            return {}
        u_mat = self.som.u_matrix().tolist() if self.som else []
        return {
            "documents": [
                {
                    "title": self.titles[i],
                    "snippet": self.documents[i][:120] + "...",
                    "row": self.positions[i]["row"],
                    "col": self.positions[i]["col"],
                    "cluster": self.labels[i],
                    "dist": self.positions[i]["dist"],
                }
                for i in range(len(self.documents))
            ],
            "top_words": self.top_words,
            "u_matrix": u_mat,
            "grid_rows": self.grid_size[0],
            "grid_cols": self.grid_size[1],
            "n_clusters": self.n_clusters,
            "qe_history": self.som.quantization_errors[-50:] if self.som else [],
            "vocab_size": len(self.vocab),
            "n_docs": len(self.documents),
        }

    def save_session(self, path: str):
        """Guarda la sesión en JSON."""
        data = {
            "titles": self.titles,
            "documents": self.documents,
            "grid_size": list(self.grid_size),
            "n_clusters": self.n_clusters,
            "max_iter": self.max_iter,
            "positions": self.positions,
            "labels": self.labels,
            "top_words": {str(k): v for k, v in self.top_words.items()},
            "som": self.som.get_state() if self.som else None,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_session(self, path: str):
        """Carga una sesión desde JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.titles = data["titles"]
        self.documents = data["documents"]
        self.grid_size = tuple(data["grid_size"])
        self.n_clusters = data["n_clusters"]
        self.max_iter = data["max_iter"]
        self.positions = data["positions"]
        self.labels = data["labels"]
        self.top_words = {int(k): v for k, v in data["top_words"].items()}
        if data["som"]:
            self.som = SOMKohonen.from_state(data["som"])
        self.prepare()


# ─── Textos de demostración ───────────────────────────────────────────────────

DEMO_STORIES = [
    ("Caperucita Roja",
     "Había una vez una niña que vivía cerca del bosque. Su abuela le había regalado una capa roja. "
     "Un día su madre le pidió llevar comida a su abuela enferma que vivía al otro lado del bosque. "
     "En el camino se encontró con un lobo feroz que le preguntó a dónde iba. El lobo llegó primero "
     "a casa de la abuela, la encerró y se disfrazó de ella. Cuando llegó la niña notó algo extraño: "
     "qué orejas tan grandes tienes, qué ojos tan grandes tienes, qué boca tan grande tienes. "
     "Llegó un cazador y rescató a la abuela del vientre del lobo."),

    ("Los Tres Cerditos",
     "Tres cerditos hermanos construyeron sus casas: el primero de paja, el segundo de madera "
     "y el tercero de ladrillos. Llegó el lobo feroz y sopló y sopló la casa de paja hasta derribarla. "
     "El cerdito corrió a casa de su hermano pero el lobo también derribó la casa de madera. "
     "Los dos cerditos corrieron a la casa de ladrillos del tercer hermano. El lobo sopló con todas "
     "sus fuerzas pero no pudo derribar la casa. Intentó entrar por la chimenea pero cayó en una "
     "olla de agua caliente y huyó para nunca más molestar a los tres cerditos."),

    ("Blancanieves",
     "Una princesa muy hermosa de cabello negro como el ébano vivía con su madrastra la malvada reina. "
     "El espejo mágico le dijo a la reina que Blancanieves era la más hermosa del reino. "
     "La reina envió a un cazador a matar a la princesa en el bosque. El cazador no pudo hacerlo "
     "y la dejó escapar. Blancanieves encontró refugio en la casa de los siete enanitos trabajadores. "
     "La reina disfrazada de anciana le ofreció una manzana envenenada. Un príncipe la encontró "
     "dormida y su beso la despertó del sueño eterno."),

    ("La Cenicienta",
     "Una joven bondadosa vivía con su cruel madrastra y sus hermanastras. Mientras ellas iban al "
     "baile del príncipe, Cenicienta debía quedarse limpiando. Su hada madrina apareció y con magia "
     "transformó una calabaza en carruaje, ratones en caballos y sus harapos en un vestido elegante. "
     "Le advirtió que debía regresar antes de la medianoche. En el baile el príncipe se enamoró de ella. "
     "Al huir perdió su zapatilla de cristal. El príncipe recorrió el reino buscando a quien le "
     "quedara la zapatilla hasta encontrar a Cenicienta."),

    ("Jack y las Habichuelas Mágicas",
     "Un niño pobre cambió su vaca por unas semillas mágicas. Su madre enojada las tiró por la ventana. "
     "Al día siguiente había crecido una enorme planta que llegaba hasta las nubes. Jack subió y "
     "encontró un castillo gigante habitado por un ogro enorme. El ogro olía la sangre de un humano. "
     "Jack robó el cofre de monedas de oro, la gallina de los huevos de oro y el arpa mágica. "
     "El ogro lo persiguió por la planta gigante pero Jack cortó la planta con un hacha y el "
     "ogro cayó al suelo. Jack y su madre vivieron felices para siempre con sus riquezas."),

    ("La Sirenita",
     "Una sirena joven vivía en el fondo del océano con su padre el Rey del Mar. Soñaba con conocer "
     "el mundo de los humanos en la superficie. Se enamoró de un príncipe humano al que salvó de "
     "ahogarse en una tormenta. Visitó a la bruja del mar quien le dio piernas a cambio de su hermosa "
     "voz. Sin poder hablar no pudo decirle al príncipe que ella lo había salvado. El príncipe se "
     "casó con otra princesa. La sirenita se convirtió en espuma del mar pero su alma ascendió."),

    ("El Patito Feo",
     "Un patito diferente a sus hermanos nació en un nido de patos. Era más grande, más gris y torpe. "
     "Todos se burlaban de él y lo rechazaban. Pasó el invierno solo y sufriendo el frío. "
     "Sobrevivió muchas dificultades vagando solo. Al llegar la primavera vio en el lago el reflejo "
     "de un hermoso cisne y no reconoció que era él mismo. Los cisnes lo invitaron a unirse a ellos. "
     "Los niños del lago exclamaron que era el cisne más bello de todos."),

    ("El Gato con Botas",
     "Un molino heredó el molinero a su hijo mayor, un asno al segundo y solo un gato al hijo menor. "
     "El gato astuto pidió unas botas y un saco. Con ingenio cazó liebres y perdices que presentó "
     "al rey como regalos del Marqués de Carabás. Convenció al rey de que su amo era un noble rico. "
     "Llegó a un castillo habitado por un ogro que podía transformarse en cualquier animal. "
     "El gato lo retó a convertirse en ratón y lo devoró. El castillo pasó a ser de su amo "
     "quien se casó con la princesa."),

    ("La Bella y la Bestia",
     "Un mercader perdido en un bosque encontró un castillo mágico con jardines hermosos. "
     "Tomó una rosa para su hija Bella y fue capturado por una bestia aterradora. "
     "Bella se ofreció a quedarse en el castillo para liberar a su padre. Poco a poco conoció "
     "la bondad y la inteligencia de la Bestia. Aprendió a ver más allá de su apariencia monstruosa. "
     "Cuando Bella declaró su amor por la Bestia el hechizo se rompió y este se transformó "
     "en un apuesto príncipe encantado."),

    ("Rapunzel",
     "Una niña con cabello dorado mágico fue encerrada por una bruja en una torre altísima sin puerta. "
     "La bruja trepaba usando su larga trenza como escalera. Un príncipe escuchó a la joven cantando "
     "y quedó enamorado de su hermosa voz. Rapunzel bajaba su cabello para que el príncipe subiera. "
     "La bruja descubrió sus visitas y cortó la trenza dorada. Desterró a Rapunzel al desierto. "
     "El príncipe cegado por la bruja vagó años hasta reencontrarse con Rapunzel cuyas lágrimas "
     "le devolvieron la vista."),

    ("El Flautista de Hamelin",
     "La ciudad de Hamelin estaba plagada de ratas que invadían casas y almacenes. "
     "Llegó un misterioso músico con una flauta mágica y prometió librar a la ciudad de las ratas. "
     "Comenzó a tocar su flauta y todas las ratas lo siguieron hipnotizadas hasta el río donde "
     "se ahogaron. Los ciudadanos se negaron a pagarle su recompensa prometida. "
     "El flautista regresó a tocar su flauta y esta vez los niños de la ciudad lo siguieron "
     "hipnotizados hacia una cueva en la montaña y nunca regresaron."),

    ("El Principito",
     "Un pequeño príncipe vive en un planeta diminuto llamado asteroide B-612. Cuida con amor "
     "una rosa vanidosa y especial que él mismo plantó. Viaja de planeta en planeta encontrando "
     "adultos extraños: el rey que ordena lo que ya va a pasar, el vanidoso que quiere ser admirado, "
     "el bebedor que bebe para olvidar que bebe, el hombre de negocios que cuenta estrellas. "
     "En la Tierra conoce a un aviador en el desierto del Sahara y a un zorro que le enseña "
     "que solo con el corazón se puede ver bien. Lo esencial es invisible a los ojos."),
]
